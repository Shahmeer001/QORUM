"""
Session Orchestration Service.
Delegates session execution across Single, Silent, and Debate modes
to the governing SessionOrchestrator.
"""
from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session

from app.board.repository import BoardRepository
from app.domain.models import SessionConfig, SessionResult
from app.orchestrator.session_orchestrator import SessionOrchestrator


class SessionService:
    """
    Session service entry point for FastAPI routes and test callers.
    Delegates execution to SessionOrchestrator.
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        board: Optional[BoardRepository] = None,
    ) -> None:
        self.db = db
        self.orchestrator = SessionOrchestrator(db=db, board=board)

    @property
    def board(self) -> BoardRepository:
        return self.orchestrator.board

    @property
    def markets_meta(self) -> dict:
        return self.orchestrator.markets_meta

    def run_session(self, config: SessionConfig) -> SessionResult:
        return self.orchestrator.run_session(config=config, monitor=True)
