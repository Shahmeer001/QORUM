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
        running_drawdown_pct: float = 0.0,
    ) -> Tuple[Action, RiskStatus, str, List[RiskEvent]]:
        """
        Risk governance with hard veto authority.

        `running_drawdown_pct` is the CURRENT drawdown of the simulated equity
        curve (peak-to-current as a % of peak) at the time of the decision.
        The orchestrator and the replay simulator compute this from the equity
        curve and pass it in; RiskLayer does NOT compute it itself.

        Veto rules:
        - If running_drawdown_pct > max_drawdown, force HOLD (capital protection).
        - If realized volatility > max_volatility, force HOLD.
        Both overrides are logged with level='override'.
        """
        events: List[RiskEvent] = []
        closes = [c.close for c in candles]
        current_vol = calculate_realized_volatility(closes)

        # Drawdown check (capital protection): force HOLD if breaching limit.
        if running_drawdown_pct > self.max_drawdown:
            note = (
                f"Drawdown ({running_drawdown_pct:.2f}%) breached limit ({self.max_drawdown:.1f}%). "
                f"Risk forced HOLD for capital protection."
            )
            events.append(
                RiskEvent(
                    time="14:32 UTC",
                    text=f"Drawdown breach ({running_drawdown_pct:.2f}% > {self.max_drawdown:.1f}%) → forced HOLD",
                    level="override",
                )
            )
            return Action.HOLD, RiskStatus.OVERRIDDEN, note, events

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
