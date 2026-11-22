"""
Unit tests for SessionOrchestrator, Quorum rules, degraded single-agent mode,
exception/timeout handling, board event logging, missing-data weights, and minimum consensus margin.
"""
from typing import List
import time
import pytest

from app.adapters.base import MarketDataAdapter
from app.adapters.synthetic import SyntheticAdapter
from app.agents.brains.rule_brain import RuleBrain
from app.agents.market_agent import MarketAgent
from app.agents.state import AgentState
from app.board.memory_repo import MemoryBoardRepository
from app.domain.enums import Action, DataStatus, Mode, MsgType, RiskStatus, Role
from app.domain.models import AgentSummary, Candle, SessionConfig
from app.orchestrator.session_orchestrator import SessionOrchestrator
from app.supervisor.accuracy import AccuracyTracker
from app.supervisor.consensus import calculate_consensus


class EmptyDataAdapter(MarketDataAdapter):
    """Adapter that returns zero candles to simulate market closure or holiday."""
    def get_candles(self, symbol: str = "BTCUSDT", limit: int = 100) -> List[Candle]:
        return []

    def get_latest(self, symbol: str = "BTCUSDT") -> Candle:
        raise ValueError("No candles available.")


class FaultyAdapter(MarketDataAdapter):
    """Adapter that raises an exception during candle retrieval."""
    def get_candles(self, symbol: str = "BTCUSDT", limit: int = 100) -> List[Candle]:
        raise RuntimeError("Simulated database connection failure in adapter.")

    def get_latest(self, symbol: str = "BTCUSDT") -> Candle:
        raise RuntimeError("Simulated failure.")


class TimeoutAdapter(MarketDataAdapter):
    """Adapter that sleeps longer than timeout to simulate network hang."""
    def get_candles(self, symbol: str = "BTCUSDT", limit: int = 100) -> List[Candle]:
        time.sleep(1.0)
        return []

    def get_latest(self, symbol: str = "BTCUSDT") -> Candle:
        time.sleep(1.0)
        raise TimeoutError("Stalled")


def test_rule_brain_empty_candles_returns_abstain():
    """RuleBrain must return ABSTAIN safely without crashing when candles are empty."""
    brain = RuleBrain()
    state = AgentState(market="CRYPTO", role=Role.CHOSEN)
    action, conf, reason, evidence = brain.recommend(state, [], {})
    assert action == Action.ABSTAIN
    assert conf == 0.0
    assert "empty" in reason.lower()
    assert evidence == []


def test_directional_tie_resolves_to_hold():
    """Equal BUY and SELL weighted votes must resolve to HOLD, not arbitrarily BUY."""
    tracker = AccuracyTracker()
    summaries = [
        AgentSummary(
            market="CRYPTO",
            role=Role.CHOSEN,
            initial=Action.BUY,
            final=Action.BUY,
            confidence=70.0,
            reason="Crypto bullish signal",
            detail="",
        ),
        AgentSummary(
            market="US",
            role=Role.CHOSEN,
            initial=Action.SELL,
            final=Action.SELL,
            confidence=70.0,
            reason="US equity bearish signal",
            detail="",
        ),
    ]
    tracker.set_accuracy("CRYPTO", 0.70)
    tracker.set_accuracy("US", 0.70)

    consensus, conf, dist = calculate_consensus(summaries, tracker)
    assert consensus == Action.HOLD
    assert dist[Action.BUY.value] == dist[Action.SELL.value]


def test_agent_abstain_propagation():
    """If an agent abstains, consensus correctly reflects active voting agents."""
    tracker = AccuracyTracker()
    summaries = [
        AgentSummary(
            market="CRYPTO",
            role=Role.CHOSEN,
            initial=Action.BUY,
            final=Action.BUY,
            confidence=75.0,
            reason="Bullish momentum",
            detail="",
        ),
        AgentSummary(
            market="US",
            role=Role.RELATED,
            initial=Action.ABSTAIN,
            final=Action.ABSTAIN,
            confidence=0.0,
            reason="Empty candle series",
            detail="",
        ),
    ]
    consensus, conf, dist = calculate_consensus(summaries, tracker)
    assert consensus == Action.BUY
    assert dist[Action.BUY.value] > 0.0


def test_orchestrator_quorum_rule_failure():
    """When < 50% of active agents have valid data, orchestrator check_quorum fails."""
    board = MemoryBoardRepository()
    orchestrator = SessionOrchestrator(board=board)

    empty_adapter = EmptyDataAdapter()
    agents = {
        "CRYPTO": MarketAgent(market="CRYPTO", adapter=empty_adapter, board=board, role=Role.CHOSEN),
        "US": MarketAgent(market="US", adapter=empty_adapter, board=board, role=Role.RELATED),
    }

    quorum_met, valid_count, total_count, reasons, valid_markets = orchestrator.check_quorum(
        agents, asset="BTCUSDT"
    )
    assert not quorum_met
    assert valid_count == 0
    assert total_count == 2
    assert len(reasons) == 2
    assert valid_markets == []


def test_orchestrator_session_halts_on_quorum_failure():
    """Full session execution halts with RiskStatus.QUORUM_NOT_MET when all agents are invalid."""
    board = MemoryBoardRepository()

    class FailingOrchestrator(SessionOrchestrator):
        def check_quorum(self, agents, asset, session_id=""):
            return False, 0, 2, ["US: empty data", "CRYPTO: empty data"], []

    fail_orch = FailingOrchestrator(board=board)
    cfg = SessionConfig(
        target="CRYPTO",
        related=["US"],
        asset="BTCUSDT",
        mode=Mode.DEBATE,
    )
    result = fail_orch.run_session(cfg, monitor=True)

    assert result.risk_status == RiskStatus.QUORUM_NOT_MET
    assert result.consensus == Action.HOLD
    assert result.final_action == Action.HOLD
    assert result.turns_used == 0
    assert result.trades == []
    assert "Quorum Not Met" in result.risk_note


def test_orchestrator_with_and_without_monitoring():
    """Demonstrates milestone: 2 agents operating WITH and WITHOUT the orchestrator."""
    board = MemoryBoardRepository()
    orchestrator = SessionOrchestrator(board=board)

    cfg = SessionConfig(
        target="US",
        related=["CRYPTO"],
        asset="SPY",
        mode=Mode.DEBATE,
        scenario="bull",
    )

    # 1. Monitored run
    res_monitored = orchestrator.run_monitored(cfg)
    assert res_monitored.risk_status in (RiskStatus.APPROVED, RiskStatus.OVERRIDDEN)
    assert res_monitored.turns_used >= 1

    # 2. Unmonitored run
    res_unmonitored = orchestrator.run_unmonitored(cfg)
    assert res_unmonitored.turns_used >= 1
    assert res_unmonitored.id != res_monitored.id


def test_debate_quorum_degraded_single_agent_on_us_holiday():
    """
    Follow-up 2: On a US Holiday, SPY has no candle but BTC does.
    Debate requires both agents; since only one is valid, orchestrator must run
    a clearly labelled degraded single-agent result and record the reason on the board.
    """
    board = MemoryBoardRepository()
    orchestrator = SessionOrchestrator(board=board)

    # Mock build_agents to simulate US closed on holiday and CRYPTO active
    class HolidayOrchestrator(SessionOrchestrator):
        def check_quorum(self, agents, asset, session_id=""):
            # US has zero candles, CRYPTO has valid candles
            self._post_orchestrator_event(
                session_id=session_id,
                reason="US market closed for Memorial Day holiday. 0 candles returned.",
                evidence=["US Holiday", "0 Candles"],
            )
            return True, 1, 2, ["US: market holiday"], ["CRYPTO"]

    holiday_orch = HolidayOrchestrator(board=board)
    cfg = SessionConfig(
        target="US",
        related=["CRYPTO"],
        asset="BTCUSDT",
        mode=Mode.DEBATE,
        scenario="bull",
    )
    result = holiday_orch.run_session(cfg, monitor=True)

    # Verified degraded single-agent execution
    assert result.mode == Mode.SINGLE
    assert result.target == "CRYPTO"
    assert "Degraded single-agent mode" in result.risk_note

    # Verify reason was recorded on the board
    board_msgs = board.get_all(result.id)
    orch_msgs = [m for m in board_msgs if m.from_market == "ORCHESTRATOR"]
    assert len(orch_msgs) >= 1
    assert any("Degraded Quorum" in m.reason or "holiday" in m.reason.lower() for m in orch_msgs)


def test_agent_exception_handled_and_logged_to_board():
    """
    Follow-up 3: When an agent raises an exception, it is caught safely,
    an error message is recorded on the board, and the agent abstains without crashing.
    """
    board = MemoryBoardRepository()
    faulty_agent = MarketAgent(
        market="US",
        adapter=FaultyAdapter(),
        board=board,
        role=Role.RELATED,
    )
    session_id = "QRM-TEST-EXC"
    msg = faulty_agent.round_0_recommend(session_id=session_id, symbol="SPY")

    assert msg.position == Action.ABSTAIN
    assert msg.confidence == 0.0
    assert "Exception" in msg.reason
    assert "RuntimeError" in msg.reason

    # Verify written to board
    all_msgs = board.get_all(session_id)
    assert len(all_msgs) == 1
    assert all_msgs[0].from_market == "US"
    assert all_msgs[0].position == Action.ABSTAIN


def test_agent_timeout_handled_and_logged_to_board():
    """
    Follow-up 3: When an agent times out, it is caught safely,
    a timeout message is recorded on the board, and the agent abstains without crashing.
    """
    board = MemoryBoardRepository()
    timeout_agent = MarketAgent(
        market="CRYPTO",
        adapter=TimeoutAdapter(),
        board=board,
        role=Role.CHOSEN,
        timeout=0.1,  # Fast 100ms timeout for test
    )
    session_id = "QRM-TEST-TO"
    msg = timeout_agent.round_0_recommend(session_id=session_id, symbol="BTCUSDT")

    assert msg.position == Action.ABSTAIN
    assert msg.confidence == 0.0
    assert "Timeout" in msg.reason

    # Verify written to board
    all_msgs = board.get_all(session_id)
    assert len(all_msgs) == 1
    assert all_msgs[0].from_market == "CRYPTO"
    assert all_msgs[0].position == Action.ABSTAIN


def test_orchestrator_health_and_quorum_events_written_to_board():
    """
    Follow-up 3: Orchestrator health check and quorum events must be written
    to the board as official messages.
    """
    board = MemoryBoardRepository()
    orchestrator = SessionOrchestrator(board=board)

    cfg = SessionConfig(
        target="US",
        related=["CRYPTO"],
        asset="SPY",
        mode=Mode.DEBATE,
        scenario="bull",
    )
    result = orchestrator.run_monitored(cfg)

    # Confirm Orchestrator messages are on the board
    board_msgs = board.get_all(result.id)
    orch_msgs = [m for m in board_msgs if m.from_market == "ORCHESTRATOR"]
    assert len(orch_msgs) >= 1
    assert any("health check passed" in m.reason.lower() for m in orch_msgs)


def test_missing_data_abstain_does_not_update_weights():
    """
    Follow-up 4 / Small fix 1: A missing-data ABSTAIN with typed DataStatus.NO_DATA
    must not update accuracy weights.
    """
    tracker = AccuracyTracker()
    initial_acc = tracker.get_accuracy("US")
    initial_weight = tracker.get_weight("US", Role.RELATED)

    # 1. Attempt to update with DataStatus.NO_DATA (typed flag)
    acc_after_no_data = tracker.record_prediction(
        market="US",
        was_correct=False,
        action=Action.ABSTAIN,
        data_status=DataStatus.NO_DATA,
    )
    assert acc_after_no_data == initial_acc
    assert tracker.get_weight("US", Role.RELATED) == initial_weight

    # 2. Attempt to update with Action.ABSTAIN
    acc_after_abstain = tracker.record_prediction(
        market="US",
        was_correct=False,
        action=Action.ABSTAIN,
        data_status=DataStatus.VALID,
    )
    assert acc_after_abstain == initial_acc
    assert tracker.get_weight("US", Role.RELATED) == initial_weight

    # 3. Valid active prediction with DataStatus.VALID DOES update
    acc_after_real_loss = tracker.record_prediction(
        market="US",
        was_correct=False,
        action=Action.BUY,
        data_status=DataStatus.VALID,
    )
    assert acc_after_real_loss < initial_acc
    assert tracker.get_weight("US", Role.RELATED) < initial_weight


def test_configurable_minimum_margin_forces_hold():
    """
    Follow-up 5: If winning score does not beat runner-up by min_margin,
    consensus defaults to HOLD.
    """
    tracker = AccuracyTracker()
    tracker.set_accuracy("CRYPTO", 0.70)
    tracker.set_accuracy("US", 0.65)

    # Narrow lead: CRYPTO votes BUY with 70%, US votes SELL with 68%
    summaries = [
        AgentSummary(
            market="CRYPTO",
            role=Role.CHOSEN,
            initial=Action.BUY,
            final=Action.BUY,
            confidence=70.0,
            reason="Bullish signal",
            detail="",
        ),
        AgentSummary(
            market="US",
            role=Role.CHOSEN,
            initial=Action.SELL,
            final=Action.SELL,
            confidence=68.0,
            reason="Bearish signal",
            detail="",
        ),
    ]

    # Without minimum margin (min_margin = 0.0), BUY edges out SELL
    consensus_zero_margin, _, dist_zero = calculate_consensus(
        summaries, tracker, min_margin=0.0
    )
    assert consensus_zero_margin == Action.BUY

    # With minimum margin of 10.0%, lead is insufficient (< 10%) -> forced to HOLD
    consensus_with_margin, _, dist_margin = calculate_consensus(
        summaries, tracker, min_margin=10.0
    )
    assert consensus_with_margin == Action.HOLD
