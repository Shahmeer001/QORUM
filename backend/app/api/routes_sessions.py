from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas import SessionCreateRequest
from app.domain.enums import Mode
from app.domain.models import SessionConfig, SessionResult
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["Sessions"])

# In-memory cache for latest active session
_LATEST_SESSION: Optional[SessionResult] = None


@router.post("", response_model=SessionResult)
def create_session(
    payload: SessionCreateRequest, db: Session = Depends(get_db)
) -> SessionResult:
    global _LATEST_SESSION
    cfg = SessionConfig(
        target=payload.target,
        related=payload.related,
        asset=payload.asset,
        horizon=payload.horizon,
        max_turns=payload.maxTurns,
        stop_loss=payload.stopLoss,
        max_vol=payload.maxVol,
        max_dd=payload.maxDD,
        notes=payload.notes,
        mode=Mode(payload.mode.lower()),
        day=payload.day,
        scenario=payload.scenario,
    )
    service = SessionService(db=db)
    result = service.run_session(cfg)
    _LATEST_SESSION = result
    return result


@router.get("/latest", response_model=SessionResult)
def get_latest_session(db: Session = Depends(get_db)) -> SessionResult:
    global _LATEST_SESSION
    if _LATEST_SESSION is not None:
        return _LATEST_SESSION
    # Create default session if none exists
    service = SessionService(db=db)
    _LATEST_SESSION = service.run_session(SessionConfig())
    return _LATEST_SESSION


@router.get("/{session_id}", response_model=SessionResult)
def get_session(session_id: str, db: Session = Depends(get_db)) -> SessionResult:
    global _LATEST_SESSION
    if _LATEST_SESSION and _LATEST_SESSION.id == session_id:
        return _LATEST_SESSION
    return get_latest_session(db=db)
