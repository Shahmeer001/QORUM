"""
Silent Consensus Mode.
All agents provide independent recommendations (Round 0) without peer challenges.
Supervisor forms weighted consensus without debate.
"""
from __future__ import annotations

from typing import Dict, List, Tuple
from app.agents.market_agent import MarketAgent
from app.board.repository import BoardRepository
from app.domain.enums import Action
from app.domain.models import AgentSummary
from app.supervisor.accuracy import AccuracyTracker
from app.supervisor.consensus import calculate_consensus
from app.supervisor.events import SupervisorEventLog


def run_silent_mode(
    agents: Dict[str, MarketAgent],
    board: BoardRepository,
    session_id: str,
    asset: str,
    min_margin: float = 0.0,
    weighted: bool = True,
    accuracy_tracker: AccuracyTracker | None = None,
) -> Tuple[int, Action, List[AgentSummary], List[SupervisorEventLog]]:
    """
    Silent consensus mode (Part 0.2).
    - weighted=True  -> silent-weighted: vote = role x learned accuracy (scaled
      by confidence). Same weights debate uses, minus the dialogue.
    - weighted=False -> silent-unweighted: equal votes (base weight 1.0, no
      role, no accuracy), scaled by confidence.
    """
    events: List[SupervisorEventLog] = []
    summaries: List[AgentSummary] = []

    for market, agent in agents.items():
        msg = agent.round_0_recommend(session_id, symbol=asset)
        summaries.append(
            AgentSummary(
                market=market,
                role=agent.role,
                initial=msg.position,
                final=msg.position,
                confidence=msg.confidence,
                reason=msg.reason,
                detail="; ".join(msg.evidence),
            )
        )

    if accuracy_tracker is None:
        accuracy_tracker = AccuracyTracker()

    events.append(
        SupervisorEventLog(
            round=0,
            text=(
                f"Silent {'weighted' if weighted else 'unweighted'} mode: "
                f"collected {len(summaries)} independent recommendations without debate."
            ),
        )
    )

    consensus, _, _ = calculate_consensus(
        summaries, accuracy_tracker, min_margin=min_margin, unweighted=not weighted
    )
    return 0, consensus, summaries, events
