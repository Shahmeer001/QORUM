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

    def set_accuracy(self, market: str, accuracy: float) -> None:
        """Sets the accuracy score directly for a given market."""
        self._accuracy[market] = max(0.0, min(1.0, float(accuracy)))

    def record_prediction(
        self, market: str, was_correct: bool, learning_rate: float = 0.08
    ) -> float:
        """
        Dynamically updates an agent's accuracy score based on past correct/wrong calls over days.
        Accuracy shifts toward 1.0 on correct calls and toward 0.0 on incorrect calls.
        """
        current = self._accuracy.get(market, 0.55)
        target = 1.0 if was_correct else 0.0
        updated = current + learning_rate * (target - current)
        updated = max(0.10, min(0.95, round(updated, 4)))
        self._accuracy[market] = updated
        return updated

    def get_accuracy(self, market: str) -> float:
        return self._accuracy.get(market, 0.55)

    def get_weight(self, market: str, role: Role) -> float:
        base = 1.5 if role == Role.CHOSEN else 1.0
        acc = self._accuracy.get(market, 0.55)
        # Weight scales smoothly with accuracy
        return round(base * (0.8 + acc * 0.4), 2)
