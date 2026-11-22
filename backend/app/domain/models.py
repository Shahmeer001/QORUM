from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import Action, MarketId, Mode, MsgType, RiskStatus, Role


class Candle(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float = 0.0


class Message(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    session_id: str = Field(default="", alias="session")
    round: int
    from_market: str = Field(default="", alias="sender")
    to_market: str = Field(default="BOARD", alias="recipient")
    msg_type: MsgType = Field(default=MsgType.RECOMMEND, alias="type")
    position: Action
    confidence: float = 50.0
    reason: str
    evidence: List[str] = Field(default_factory=list)
    is_visible: bool = True
    created_at: Optional[str] = Field(default=None, alias="posted_time")

    @property
    def sender(self) -> str:
        return self.from_market

    @property
    def recipient(self) -> str:
        return self.to_market

    @property
    def session(self) -> str:
        return self.session_id


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
    markets: List[str] = Field(default_factory=list)
    asset: str = "XAUUSD"
    horizon: str = "Swing"
    max_turns: int = 3
    stop_loss: float = 1.2
    max_vol: float = 2.5
    max_dd: float = 5.0
    risk_limits: Dict[str, float] = Field(default_factory=dict)
    allow_short: bool = True
    notes: str = ""
    mode: Mode = Mode.DEBATE
    day: str = "2026-11-10"
    scenario: str = "neutral"  # "bull", "bear", "neutral"
    min_margin: float = 0.0    # % minimum lead over runner-up required for directional consensus

    def model_post_init(self, __context: Any) -> None:
        if not self.markets:
            self.markets = [self.target] + [m for m in self.related if m != self.target]
        if not self.risk_limits:
            self.risk_limits = {
                "stop_loss": self.stop_loss,
                "max_vol": self.max_vol,
                "max_dd": self.max_dd,
            }


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
