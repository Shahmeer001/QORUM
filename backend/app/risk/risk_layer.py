"""
QUORUM Risk Layer.
Holds absolute veto authority over the supervisor's recommended consensus.
Applies volatility filters, drawdown stops, and capital protection rules.
"""
from __future__ import annotations

from typing import List, Tuple
from app.domain.enums import Action, RiskStatus
from app.domain.models import Candle, RiskEvent
from app.signals.volatility import calculate_realized_volatility


class RiskLayer:
    def __init__(
        self,
        stop_loss: float = 1.2,
        max_volatility: float = 2.5,
        max_drawdown: float = 5.0,
    ) -> None:
        self.stop_loss = stop_loss
        self.max_volatility = max_volatility
        self.max_drawdown = max_drawdown

    def evaluate(
        self,
        consensus: Action,
        candles: List[Candle],
        historical_drawdown: float = 1.1,
    ) -> Tuple[Action, RiskStatus, str, List[RiskEvent]]:
        events: List[RiskEvent] = []
        closes = [c.close for c in candles]
        current_vol = calculate_realized_volatility(closes)

        # Baseline checks
        if historical_drawdown <= self.max_drawdown:
            events.append(
                RiskEvent(
                    time="10:00 UTC",
                    text=f"Historical drawdown {historical_drawdown:.1f}% — within {self.max_drawdown:.1f}% limit",
                    level="ok",
                )
            )

        # Volatility check: if volatility exceeds threshold, override BUY/SELL to HOLD
        if current_vol > self.max_volatility and consensus in (Action.BUY, Action.SELL):
            note = (
                f"Overridden from {consensus.value} to HOLD — realized volatility ({current_vol:.1f}%) "
                f"exceeded maximum allowed limit ({self.max_volatility:.1f}%)."
            )
            events.append(
                RiskEvent(
                    time="14:32 UTC",
                    text=f"Volatility threshold exceeded ({current_vol:.1f}% > {self.max_volatility:.1f}%) → override to HOLD",
                    level="override",
                )
            )
            return Action.HOLD, RiskStatus.OVERRIDDEN, note, events

        # Drawdown check: if drawdown breaches max_drawdown, override to ABSTAIN
        if historical_drawdown > self.max_drawdown:
            note = f"Drawdown ({historical_drawdown:.1f}%) breached limit ({self.max_drawdown:.1f}%). Risk forced ABSTAIN."
            events.append(
                RiskEvent(
                    time="14:32 UTC",
                    text=f"Drawdown breach ({historical_drawdown:.1f}% > {self.max_drawdown:.1f}%) → forced ABSTAIN",
                    level="override",
                )
            )
            return Action.ABSTAIN, RiskStatus.OVERRIDDEN, note, events

        # If passed without override
        events.append(
            RiskEvent(
                time="14:32 UTC",
                text="All risk checks passed — consensus action approved.",
                level="ok",
            )
        )
        return (
            consensus,
            RiskStatus.APPROVED,
            f"Risk control approved {consensus.value} with volatility at {current_vol:.1f}%.",
            events,
        )
