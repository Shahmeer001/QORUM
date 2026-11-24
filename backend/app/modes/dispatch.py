"""
Single dispatcher for all comparison modes (Part 0.2).

Mode -> runner mapping:
- SINGLE              : only the target (CHOSEN) agent evaluates the asset.
- SILENT_UNWEIGHTED   : equal votes (no role, no accuracy) + no dialogue.
- SILENT / SILENT_WEIGHTED : role x learned accuracy + no dialogue.
- DEBATE              : role x learned accuracy + the structured dialogue.

Both the orchestrator and the replay simulator call this so the mode
definitions stay in exactly one place.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from app.agents.market_agent import MarketAgent
from app.board.repository import BoardRepository
from app.domain.enums import Action, Mode
from app.domain.models import AgentSummary
from app.modes.debate import run_debate_mode
from app.modes.silent import run_silent_mode
from app.modes.single import run_single_mode
from app.supervisor.accuracy import AccuracyTracker
from app.supervisor.events import SupervisorEventLog


def run_mode(
    mode: Mode,
    agents: Dict[str, MarketAgent],
    board: BoardRepository,
    session_id: str,
    asset: str,
    max_turns: int = 3,
    min_margin: float = 0.0,
    target_market: Optional[str] = None,
    accuracy_tracker: Optional[AccuracyTracker] = None,
) -> Tuple[int, Action, List[AgentSummary], List[SupervisorEventLog]]:
    if mode == Mode.SINGLE:
        return run_single_mode(
            agents=agents,
            board=board,
            session_id=session_id,
            target_market=target_market or "",
            asset=asset,
        )
    if mode == Mode.SILENT_UNWEIGHTED:
        return run_silent_mode(
            agents=agents,
            board=board,
            session_id=session_id,
            asset=asset,
            min_margin=min_margin,
            weighted=False,
            accuracy_tracker=accuracy_tracker,
        )
    if mode in (Mode.SILENT, Mode.SILENT_WEIGHTED):
        return run_silent_mode(
            agents=agents,
            board=board,
            session_id=session_id,
            asset=asset,
            min_margin=min_margin,
            weighted=True,
            accuracy_tracker=accuracy_tracker,
        )
    # Mode.DEBATE
    return run_debate_mode(
        agents=agents,
        board=board,
        session_id=session_id,
        asset=asset,
        max_turns=max_turns,
        min_margin=min_margin,
        accuracy_tracker=accuracy_tracker,
    )
