"""
Single Agent Mode.
Only the target market's CHOSEN agent evaluates the asset in isolation. No debate.
"""
from __future__ import annotations

from typing import Dict, List, Tuple
from app.agents.market_agent import MarketAgent
from app.board.repository import BoardRepository
from app.domain.enums import Action, Role
from app.domain.models import AgentSummary
from app.supervisor.events import SupervisorEventLog


def run_single_mode(
    agents: Dict[str, MarketAgent],
    board: BoardRepository,
    session_id: str,
    target_market: str,
    asset: str,
) -> Tuple[int, Action, List[AgentSummary], List[SupervisorEventLog]]:
    target_agent = agents[target_market]
    msg = target_agent.round_0_recommend(session_id, symbol=asset)

    events = [
        SupervisorEventLog(
            round=0,
            text=f"Single-agent mode executed: {target_market} analyzed {asset} in isolation.",
        )
    ]

    summary = AgentSummary(
        market=target_market,
        role=Role.CHOSEN,
        initial=msg.position,
        final=msg.position,
        confidence=msg.confidence,
        reason=msg.reason,
        detail="; ".join(msg.evidence),
    )

    return 0, msg.position, [summary], events
