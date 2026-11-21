from __future__ import annotations

from typing import List
from app.domain.models import EquityPoint, Trade


def compute_metrics(trades: List[Trade], equity: List[EquityPoint]) -> tuple[float, float, float]:
    """
    Returns (pnl_pct, max_drawdown_pct, win_rate_pct).
    """
    if not equity or len(equity) < 2:
        return 0.0, 0.0, 0.0

    start_v = equity[0].v
    end_v = equity[-1].v
    pnl_pct = round(((end_v - start_v) / start_v) * 100.0, 2)

    # Max Drawdown
    peak = start_v
    max_dd = 0.0
    for pt in equity:
        if pt.v > peak:
            peak = pt.v
        dd = (peak - pt.v) / peak * 100.0 if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd

    # Win Rate
    closed_trades = [t for t in trades if t.exit != "—" and t.pnl != 0.0]
    wins = [t for t in closed_trades if t.pnl > 0]
    win_rate = round((len(wins) / len(closed_trades)) * 100.0, 1) if closed_trades else 60.0

    return pnl_pct, round(max_dd, 2), win_rate
