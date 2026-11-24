"""
Tests for Part 0.2 (mode definitions): silent-unweighted vs silent-weighted vs debate.
"""
from __future__ import annotations

from app.adapters.synthetic import SyntheticAdapter
from app.agents.brains.fake_brain import FakeBrain
from app.agents.market_agent import MarketAgent
from app.board.memory_repo import MemoryBoardRepository
from app.domain.enums import Action, MsgType, Role
from app.modes.debate import run_debate_mode
from app.modes.silent import run_silent_mode
from app.supervisor.accuracy import AccuracyTracker
from app.supervisor.consensus import calculate_consensus
from app.domain.models import AgentSummary


def _agents(forced_us: Action, forced_crypto: Action):
    """Two agents (US=CHOSEN, CRYPTO=RELATED) backed by FakeBrain + synthetic data."""
    board = MemoryBoardRepository()
    return {
        "US": MarketAgent(
            market="US", adapter=SyntheticAdapter("neutral", 100.0), board=board,
            role=Role.CHOSEN, brain=FakeBrain(forced_us),
        ),
        "CRYPTO": MarketAgent(
            market="CRYPTO", adapter=SyntheticAdapter("neutral", 100.0), board=board,
            role=Role.RELATED, brain=FakeBrain(forced_crypto),
        ),
    }, board


def test_unweighted_ignores_role_and_accuracy():
    """Equal votes: a CHOSEN high-accuracy SELL ties a RELATED low-accuracy BUY -> HOLD."""
    tracker = AccuracyTracker()
    tracker.set_accuracy("US", 0.95)     # CHOSEN, high accuracy
    tracker.set_accuracy("CRYPTO", 0.10)  # RELATED, low accuracy
    summaries = [
        AgentSummary(market="US", role=Role.CHOSEN, initial=Action.SELL, final=Action.SELL,
                     confidence=70.0, reason="", detail=""),
        AgentSummary(market="CRYPTO", role=Role.RELATED, initial=Action.BUY, final=Action.BUY,
                     confidence=70.0, reason="", detail=""),
    ]
    weighted, _, _ = calculate_consensus(summaries, tracker, unweighted=False)
    assert weighted == Action.SELL  # role x accuracy favours US CHOSEN

    unweighted, _, _ = calculate_consensus(summaries, tracker, unweighted=True)
    assert unweighted == Action.HOLD  # equal votes -> directional tie -> HOLD


def test_weighted_resolves_by_role_x_accuracy():
    """When the high-weight agent is BUY, weighted consensus is BUY; unweighted still ties."""
    tracker = AccuracyTracker()
    tracker.set_accuracy("US", 0.95)
    tracker.set_accuracy("CRYPTO", 0.10)
    summaries = [
        AgentSummary(market="US", role=Role.CHOSEN, initial=Action.BUY, final=Action.BUY,
                     confidence=70.0, reason="", detail=""),
        AgentSummary(market="CRYPTO", role=Role.RELATED, initial=Action.SELL, final=Action.SELL,
                     confidence=70.0, reason="", detail=""),
    ]
    weighted, _, _ = calculate_consensus(summaries, tracker, unweighted=False)
    assert weighted == Action.BUY

    unweighted, _, _ = calculate_consensus(summaries, tracker, unweighted=True)
    assert unweighted == Action.HOLD


def test_debate_uses_same_weights_as_silent_weighted():
    """With identical agents and the same learned weights, debate and silent-weighted
    agree on the directional consensus; debate additionally produces dialogue."""
    tracker = AccuracyTracker()
    tracker.set_accuracy("US", 0.90)
    tracker.set_accuracy("CRYPTO", 0.20)

    agents_s, board_s = _agents(Action.BUY, Action.SELL)
    agents_d, board_d = _agents(Action.BUY, Action.SELL)

    _, cons_s, _, _ = run_silent_mode(
        agents_s, board_s, "sess-silent", "XAUUSD",
        weighted=True, accuracy_tracker=tracker,
    )
    _, cons_d, _, _ = run_debate_mode(
        agents_d, board_d, "sess-debate", "XAUUSD",
        max_turns=3, min_margin=0.0, accuracy_tracker=tracker,
    )

    # Same weights -> same directional outcome (CHOSEN high-accuracy US BUY wins).
    assert cons_s == Action.BUY
    assert cons_d == Action.BUY

    # Debate adds dialogue (challenges / replies / finals) beyond silent recommendations.
    silent_types = {m.msg_type for m in board_s.get_all("sess-silent")}
    debate_types = {m.msg_type for m in board_d.get_all("sess-debate")}
    assert silent_types == {MsgType.RECOMMEND}
    assert MsgType.CHALLENGE in debate_types
    assert MsgType.REPLY in debate_types
    assert MsgType.FINAL in debate_types
    assert len(board_d.get_all("sess-debate")) > len(board_s.get_all("sess-silent"))


def test_silent_unweighted_tie_does_not_tie_when_votes_differ():
    """Unweighted with a clear 2-vs-1 majority is not a tie."""
    tracker = AccuracyTracker()
    summaries = [
        AgentSummary(market="US", role=Role.CHOSEN, initial=Action.BUY, final=Action.BUY,
                     confidence=70.0, reason="", detail=""),
        AgentSummary(market="CRYPTO", role=Role.RELATED, initial=Action.BUY, final=Action.BUY,
                     confidence=70.0, reason="", detail=""),
        AgentSummary(market="PSX", role=Role.RELATED, initial=Action.SELL, final=Action.SELL,
                     confidence=70.0, reason="", detail=""),
    ]
    consensus, _, _ = calculate_consensus(summaries, tracker, unweighted=True)
    assert consensus == Action.BUY  # 2 BUY vs 1 SELL -> BUY, not a tie
