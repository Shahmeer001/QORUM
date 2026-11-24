from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from app.domain.enums import Action, DataStatus, Role
from app.domain.models import Message


@dataclass
class AgentState:
    market: str
    role: Role = Role.RELATED
    current_position: Action = Action.HOLD
    confidence: float = 50.0
    last_reason: str = ""
    evidence: List[str] = field(default_factory=list)
    received_challenges: List[Message] = field(default_factory=list)
    # Typed data status from the agent's most recent recommendation round.
    # Used by accuracy bookkeeping to exclude non-VALID calls.
    data_status: DataStatus = DataStatus.VALID
