"""
Debate Mode.
Full multi-agent structured debate with challenges, replies, and final consensus.
"""
from __future__ import annotations

from typing import Dict, List, Tuple
from app.agents.market_agent import MarketAgent
from app.board.repository import BoardRepository
from app.domain.enums import Action
from app.domain.models import AgentSummary
from app.supervisor.debate_loop import DebateLoop
from app.supervisor.events import SupervisorEventLog


def run_debate_mode(
    agents: Dict[str, MarketAgent],
    board: BoardRepository,
    session_id: str,
    asset: str,
    max_turns: int = 3,
    min_margin: float = 0.0,
) -> Tuple[int, Action, List[AgentSummary], List[SupervisorEventLog]]:
    loop = DebateLoop(agents=agents, board=board, max_turns=max_turns, min_margin=min_margin)
    return loop.run(session_id=session_id, asset=asset)
