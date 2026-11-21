from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.domain.enums import Action, Mode, MsgType, RiskStatus, Role
from app.domain.models import AgentSummary, EquityPoint, Message, RiskEvent, Trade


class MarketInfoSchema(BaseModel):
    id: str
    name: str
    region: str
    assets: List[str]
    open: bool
    why: str


class SessionCreateRequest(BaseModel):
    target: str = "GOLD"
    related: List[str] = ["PSX", "US", "FOREX", "CRYPTO"]
    asset: str = "XAUUSD"
    horizon: str = "Swing"
    maxTurns: int = 3
    stopLoss: float = 1.2
    maxVol: float = 2.5
    maxDD: float = 5.0
    notes: str = ""
    mode: str = "debate"
    day: str = "2026-11-10"
    scenario: str = "neutral"


class CompareSetupSchema(BaseModel):
    name: str
    id: str
    markets: List[str]
    action: Action
    turns: int
    override: bool
    pnl: float
    drawdown: float
    messages: int
