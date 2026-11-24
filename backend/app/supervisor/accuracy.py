"""
Supervisor Agent Accuracy & Weight Tracking.
Maintains historical accuracy scores and assigns voting weights.

Design (Part 0.1):
- Priors are NEUTRAL (0.5) for every market, loaded from markets.yaml
  (`accuracy_prior`). The previous invented priors (US 0.71, CRYPTO 0.55, ...)
  are removed so that weights are earned from realised outcomes, not assumed.
- Accuracy is updated by `record_prediction` only when data is VALID and the
  action is not ABSTAIN. Missing-data / error / timeout / abstain calls never
  move the weight, so they cannot distort the weighted consensus.
"""
from __future__ import annotations

from typing import Dict, Optional
import yaml

from app.config.settings import BASE_DIR
from app.domain.enums import Action, DataStatus, Role

# Neutral prior: every market starts at 50% accuracy and earns its weight.
NEUTRAL_PRIOR = 0.5


def _load_priors_from_markets() -> Dict[str, float]:
    """Read `accuracy_prior` per market from markets.yaml (defaults to neutral)."""
    priors: Dict[str, float] = {}
    config_path = BASE_DIR / "app" / "config" / "markets.yaml"
    if config_path.exists():
        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")).get("markets", {})
            for m_id, m_cfg in data.items():
                priors[str(m_id).upper()] = float(m_cfg.get("accuracy_prior", NEUTRAL_PRIOR))
        except Exception:
            pass
    return priors


class AccuracyTracker:
    def __init__(self, priors: Optional[Dict[str, float]] = None) -> None:
        # Start from configured (neutral) priors, then allow caller overrides.
        base = _load_priors_from_markets()
        if priors:
            base.update({str(k).upper(): float(v) for k, v in priors.items()})
        self._accuracy: Dict[str, float] = dict(base)

    def set_accuracy(self, market: str, accuracy: float) -> None:
        """Sets the accuracy score directly for a given market."""
        self._accuracy[market] = max(0.0, min(1.0, float(accuracy)))

    def record_prediction(
        self,
        market: str,
        was_correct: Optional[bool] = None,
        action: Optional[Action] = None,
        data_status: DataStatus = DataStatus.VALID,
        learning_rate: float = 0.08,
    ) -> float:
        """
        Dynamically updates an agent's accuracy score based on past correct/wrong calls over days.
        Accuracy shifts toward 1.0 on correct calls and toward 0.0 on incorrect calls.
        A missing-data (DataStatus.NO_DATA), error, timeout, or ABSTAIN call MUST NOT update accuracy weights.
        """
        if data_status != DataStatus.VALID or action == Action.ABSTAIN or was_correct is None:
            return self.get_accuracy(market)

        current = self._accuracy.get(market, NEUTRAL_PRIOR)
        target = 1.0 if was_correct else 0.0
        updated = current + learning_rate * (target - current)
        updated = max(0.10, min(0.95, round(updated, 4)))
        self._accuracy[market] = updated
        return updated

    def get_accuracy(self, market: str) -> float:
        return self._accuracy.get(market, NEUTRAL_PRIOR)

    def snapshot(self) -> Dict[str, float]:
        """Return a copy of all current accuracy scores."""
        return dict(self._accuracy)

    def get_weight(self, market: str, role: Role) -> float:
        base = 1.5 if role == Role.CHOSEN else 1.0
        acc = self._accuracy.get(market, NEUTRAL_PRIOR)
        # Weight scales smoothly with accuracy
        return round(base * (0.8 + acc * 0.4), 2)
