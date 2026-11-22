"""
Simulation and Execution Performance Metrics.
Strict, evidence-based metrics computation. No fabricated or default assumptions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List
from app.domain.models import EquityPoint, Trade


@dataclass
class PerformanceSummary:
    start_equity: float
    end_equity: float
    pnl_dollars: float
    pnl_pct: float
    max_drawdown_pct: float
    hit_rate_pct: float
    exposure_pct: float
    trade_count: int
    turnover: float


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

    # Win Rate / Hit Rate: strictly 0.0 if no closed trades
    closed_trades = [t for t in trades if t.exit not in ("—", "") and t.pnl != 0.0]
    wins = [t for t in closed_trades if t.pnl > 0]
    win_rate = round((len(wins) / len(closed_trades)) * 100.0, 1) if closed_trades else 0.0

    return pnl_pct, round(max_dd, 2), win_rate


def compute_full_metrics(
    trades: List[Trade],
    equity: List[EquityPoint],
    total_days: int,
    days_exposed: int,
    total_volume_traded: float,
    initial_capital: float,
) -> PerformanceSummary:
    """Computes full quantitative trading metrics."""
    if not equity:
        return PerformanceSummary(
            start_equity=initial_capital,
            end_equity=initial_capital,
            pnl_dollars=0.0,
            pnl_pct=0.0,
            max_drawdown_pct=0.0,
            hit_rate_pct=0.0,
            exposure_pct=0.0,
            trade_count=0,
            turnover=0.0,
        )

    start_v = equity[0].v
    end_v = equity[-1].v
    pnl_dollars = round(end_v - start_v, 2)
    pnl_pct = round(((end_v - start_v) / start_v) * 100.0, 2)

    peak = start_v
    max_dd = 0.0
    for pt in equity:
        if pt.v > peak:
            peak = pt.v
        dd = (peak - pt.v) / peak * 100.0 if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd

    closed_trades = [t for t in trades if t.exit not in ("—", "") and t.pnl != 0.0]
    wins = [t for t in closed_trades if t.pnl > 0]
    hit_rate = round((len(wins) / len(closed_trades)) * 100.0, 1) if closed_trades else 0.0

    exposure_pct = round((days_exposed / total_days) * 100.0, 1) if total_days > 0 else 0.0
    turnover = round(total_volume_traded / initial_capital, 2) if initial_capital > 0 else 0.0

    return PerformanceSummary(
        start_equity=round(start_v, 2),
        end_equity=round(end_v, 2),
        pnl_dollars=pnl_dollars,
        pnl_pct=pnl_pct,
        max_drawdown_pct=round(max_dd, 2),
        hit_rate_pct=hit_rate,
        exposure_pct=exposure_pct,
        trade_count=len(closed_trades),
        turnover=turnover,
    )
