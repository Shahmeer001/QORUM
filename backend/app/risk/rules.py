from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from app.domain.enums import Action


@dataclass
class RiskCheckResult:
    passed: bool
    rule_name: str
    action_override: Optional[Action]
    reason: str
