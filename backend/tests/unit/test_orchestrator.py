"""
Unit tests for the SessionOrchestrator, Quorum Rule, empty candle guards, and tie-breaking.
"""
from typing import List
import pytest

from app.adapters.base import MarketDataAdapter
from app.agents.brains.rule_brain import RuleBrain
from app.agents.market_agent import MarketAgent
from app.agents.state import AgentState
from app.board.memory_repo import MemoryBoardRepository
from app.domain.enums import Action, Mode, RiskStatus, Role
from app.domain.models import AgentSummary, Candle, SessionConfig
from app.orchestrator.session_orchestrator import SessionOrchestrator
from app.supervisor.accuracy import AccuracyTracker
from app.supervisor.consensus import calculate_consensus


class EmptyDataAdapter(MarketDataAdapter):
    """Adapter that returns zero candles to simulate data outage."""
    def get_candles(self, symbol: str = "BTCUSDT", limit: int = 100) -> List[Candle]:
        return []

    def get_latest(self, symbol: str = "BTCUSDT") -> Candle:
        raise ValueError("No candles available.")


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
    # Both agents have equal weight and equal confidence, one BUY, one SELL
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
    # Equalize tracker weights
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
    """When < 50% of active agents have valid data, orchestrator halts session to HOLD."""
    board = MemoryBoardRepository()
    orchestrator = SessionOrchestrator(board=board)

    # Construct mock agents where ALL have empty data
    empty_adapter = EmptyDataAdapter()
    agents = {
        "CRYPTO": MarketAgent(market="CRYPTO", adapter=empty_adapter, board=board, role=Role.CHOSEN),
        "US": MarketAgent(market="US", adapter=empty_adapter, board=board, role=Role.RELATED),
    }

    quorum_met, valid_count, total_count, reasons = orchestrator.check_quorum(agents, asset="BTCUSDT")
    assert not quorum_met
    assert valid_count == 0
    assert total_count == 2
    assert len(reasons) == 2


def test_orchestrator_session_halts_on_quorum_failure():
    """Full session execution halts with RiskStatus.QUORUM_NOT_MET when quorum is not met."""
    board = MemoryBoardRepository()
    orchestrator = SessionOrchestrator(board=board)

    # Subclass orchestrator to inject empty adapters
    class FailingOrchestrator(SessionOrchestrator):
        def check_quorum(self, agents, asset):
            return False, 0, 2, ["US: empty data", "CRYPTO: empty data"]

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

    # 1. Monitored run (with orchestrator)
    res_monitored = orchestrator.run_monitored(cfg)
    assert res_monitored.risk_status in (RiskStatus.APPROVED, RiskStatus.OVERRIDDEN)
    assert res_monitored.turns_used >= 1

    # 2. Unmonitored run (without orchestrator monitoring)
    res_unmonitored = orchestrator.run_unmonitored(cfg)
    assert res_unmonitored.turns_used >= 1
    assert res_unmonitored.id != res_monitored.id
