"""
Supervisor Agent Accuracy & Weight Tracking.
Maintains historical accuracy scores and assigns voting weights.
"""
from __future__ import annotations

from typing import Dict
from app.domain.enums import Role


class AccuracyTracker:
    def __init__(self) -> None:
        # Initial accuracy scores per market (percentage of historical correct calls)
        self._accuracy: Dict[str, float] = {
            "GOLD": 0.64,
            "US": 0.71,
            "FOREX": 0.58,
            "CRYPTO": 0.55,
            "PSX": 0.52,
        }

    def get_weight(self, market: str, role: Role) -> float:
        base = 1.5 if role == Role.CHOSEN else 1.0
        acc = self._accuracy.get(market, 0.55)
        # Weight scales smoothly with accuracy
        return round(base * (0.8 + acc * 0.4), 2)
