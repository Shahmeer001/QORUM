from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from app.domain.enums import Action, Mode, MsgType, RiskStatus, Role


class Candle(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float = 0.0


class Message(BaseModel):
    id: str
    session_id: str
    round: int
    from_market: str
    to_market: str  # Market name or 'BOARD'
    msg_type: MsgType
    position: Action
    confidence: float = 50.0
    reason: str
    evidence: List[str] = Field(default_factory=list)
    is_visible: bool = True
    created_at: Optional[str] = None


class AgentSummary(BaseModel):
    market: str
    role: Role
    initial: Action
    final: Action
    confidence: float
    reason: str
    detail: str


class SessionConfig(BaseModel):
    target: str = "GOLD"
    related: List[str] = Field(default_factory=lambda: ["PSX", "US", "FOREX", "CRYPTO"])
    asset: str = "XAUUSD"
    horizon: str = "Swing"
    max_turns: int = 3
    stop_loss: float = 1.2
    max_vol: float = 2.5
    max_dd: float = 5.0
    notes: str = ""
    mode: Mode = Mode.DEBATE
    day: str = "2026-11-10"
    scenario: str = "neutral"  # "bull", "bear", "neutral"


class Trade(BaseModel):
    entry: str
    exit: str
    side: Action
    market: str
    pnl: float
    note: str


class EquityPoint(BaseModel):
    t: str
    v: float


class RiskEvent(BaseModel):
    time: str
    text: str
    level: str  # 'ok', 'warn', 'override'


class SessionResult(BaseModel):
    id: str
    run_id: Optional[str] = None
    mode: Mode
    target: str
    asset: str
    horizon: str
    day: str
    max_turns: int
    turns_used: int
    consensus: Action
    final_action: Action
    risk_status: RiskStatus
    risk_note: str
    pnl: float
    max_drawdown: float
    win_rate: float
    timestamp: str
    messages: List[Message] = Field(default_factory=list)
    agents: List[AgentSummary] = Field(default_factory=list)
    trades: List[Trade] = Field(default_factory=list)
    equity: List[EquityPoint] = Field(default_factory=list)
    risk_events: List[RiskEvent] = Field(default_factory=list)
