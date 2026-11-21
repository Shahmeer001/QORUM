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
) -> Tuple[int, Action, List[AgentSummary], List[SupervisorEventLog]]:
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

    events.append(
        SupervisorEventLog(
            round=0,
            text=f"Silent mode: Collected {len(summaries)} independent recommendations without debate.",
        )
    )

    accuracy_tracker = AccuracyTracker()
    consensus, _, _ = calculate_consensus(summaries, accuracy_tracker)
    return 0, consensus, summaries, events
