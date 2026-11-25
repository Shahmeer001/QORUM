"""
Simulation and Execution Performance Metrics.
Strict, evidence-based metrics computation. No fabricated or default assumptions.

Definitions:
- Hit Rate (%): Percentage of completed round-trip trades with Net Realized PnL > 0.
  Hit Rate = (Winning Trades / Total Closed Trades) * 100%. (0.0% if no closed trades).
- Turnover: Total traded dollar volume (sum of all entry and exit execution notionals)
  divided by initial capital.  Turnover = Total Traded Volume / Initial Capital.
- Buy-and-Hold Exposure-Scaled Return (%): the buy-and-hold benchmark return
  scaled to the strategy's exposure level (benchmark_return_pct * exposure_ratio).
  This replaces the old "exposure-adjusted return" (return / exposure), which
  inflated strategy returns. Comparing the strategy return to the buy-and-hold
  return *at the same exposure* is the fair benchmark.
- Annualized Sharpe Ratio: Mean daily percentage return divided by standard
  deviation of daily returns, annualized by sqrt(252). Because the standard
  deviation is strictly positive, sign(Sharpe) == sign(mean daily return): a
  falling equity curve (negative mean daily return) always yields a negative
  Sharpe. If std dev == 0, returns 0.0.
"""
from __future__ import annotations

import math
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
    buy_hold_exposure_scaled_return_pct: float
    sharpe_ratio: float
    trade_count: int
    turnover: float
    trading_days_count: int


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
    benchmark_buy_hold_return_pct: float = 0.0,
) -> PerformanceSummary:
    """Computes full quantitative trading metrics including Sharpe and buy-and-hold exposure-scaled return."""
    if not equity:
        return PerformanceSummary(
            start_equity=initial_capital,
            end_equity=initial_capital,
            pnl_dollars=0.0,
            pnl_pct=0.0,
            max_drawdown_pct=0.0,
            hit_rate_pct=0.0,
            exposure_pct=0.0,
            buy_hold_exposure_scaled_return_pct=0.0,
            sharpe_ratio=0.0,
            trade_count=0,
            turnover=0.0,
            trading_days_count=total_days,
        )

    # Return is measured from initial capital: the first equity point may already
    # include entry costs. Drawdown and daily returns still follow the curve.
    start_v = initial_capital
    end_v = equity[-1].v
    pnl_dollars = round(end_v - start_v, 2)
    pnl_pct = round(((end_v - start_v) / start_v) * 100.0, 2)

    peak = equity[0].v
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

    # Buy-and-hold return scaled to the strategy's exposure level (e.g. B&H * exposure_ratio)
    exposure_ratio = days_exposed / total_days if total_days > 0 else 0.0
    bh_scaled_return = round(benchmark_buy_hold_return_pct * exposure_ratio, 2)

    # Daily returns for Sharpe Ratio
    daily_returns = []
    for i in range(1, len(equity)):
        prev = equity[i - 1].v
        curr = equity[i].v
        ret = (curr - prev) / prev if prev > 0 else 0.0
        daily_returns.append(ret)

    if len(daily_returns) > 1:
        mean_ret = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean_ret) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        std_dev = math.sqrt(variance)
        if std_dev > 1e-8:
            # Annualized Sharpe (252 trading days/year). Because std_dev is
            # strictly positive, sign(Sharpe) == sign(mean daily return) by
            # construction, which is the requirement: a falling equity curve
            # (negative mean daily return) must yield a negative Sharpe.
            sharpe = round((mean_ret / std_dev) * math.sqrt(252), 2)
        else:
            sharpe = 0.0
    else:
        sharpe = 0.0

    turnover = round(total_volume_traded / initial_capital, 2) if initial_capital > 0 else 0.0

    return PerformanceSummary(
        start_equity=round(start_v, 2),
        end_equity=round(end_v, 2),
        pnl_dollars=pnl_dollars,
        pnl_pct=pnl_pct,
        max_drawdown_pct=round(max_dd, 2),
        hit_rate_pct=hit_rate,
        exposure_pct=exposure_pct,
        buy_hold_exposure_scaled_return_pct=bh_scaled_return,
        sharpe_ratio=sharpe,
        trade_count=len(closed_trades),
        turnover=turnover,
        trading_days_count=total_days,
    )
