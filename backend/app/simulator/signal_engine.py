"""
Shared long/flat execution loop for baselines that have precomputed signals.
Same fills, friction and equity marking as BarByBarSimulator.
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional, Sequence, Tuple

from app.config.settings import INITIAL_CAPITAL, get_us_close_utc
from app.domain.enums import Action
from app.domain.models import EquityPoint, Trade
from app.simulator.metrics import PerformanceSummary, compute_full_metrics
from app.simulator.trade_engine import calculate_trade_pnl, execute_fill, get_market_friction


def price_arrays(sim, target: str, days: Sequence[date]) -> Tuple[List[float], List[float]]:
    """(fill price, close mark) per decision day. US fills at the next day's open
    (last day: its close); CRYPTO at the first 1h open at the cutoff."""
    fills: List[float] = []
    closes: List[float] = []
    if target.upper() == "US":
        rows = {r["parsed_date"]: r for _, r in sim.spy_df.iterrows()}
        for i, d in enumerate(days):
            closes.append(float(rows[d]["Close"]))
            fills.append(float(rows[days[i + 1]]["Open"]) if i + 1 < len(days) else closes[-1])
    else:
        for d in days:
            cutoff = get_us_close_utc(d.isoformat())
            closes.append(float(sim.btc_df[sim.btc_df["close_dt"] <= cutoff].iloc[-1]["Close"]))
            nxt = sim.btc_df[sim.btc_df["open_dt"] >= cutoff].head(1)
            fills.append(float(nxt.iloc[0]["Open"]) if len(nxt) else closes[-1])
    return fills, closes


def simulate_positions(
    target: str,
    days: Sequence[date],
    positions: Sequence[Optional[int]],
    fills: Sequence[float],
    closes: Sequence[float],
    initial_capital: float = INITIAL_CAPITAL,
) -> PerformanceSummary:
    """positions[i]: 1 long, 0 flat, None keep. Any open position is closed at the
    last close."""
    target = target.upper()
    friction = get_market_friction(target)
    n = len(days)
    cash, units, entry_fill, entry_time = initial_capital, 0.0, 0.0, ""
    volume, exposed = 0.0, 0
    trades: List[Trade] = []
    equity: List[EquityPoint] = []

    def close_position(raw: float, when: str) -> None:
        nonlocal cash, units, volume
        fill = execute_fill(Action.SELL, raw, friction, is_entry=False)
        pnl, _, _ = calculate_trade_pnl(entry_fill, fill, units, friction)
        notional = units * fill
        cash += notional * (1 - friction.commission)
        volume += notional
        trades.append(Trade(entry=entry_time, exit=when, side=Action.BUY,
                            market=target, pnl=round(pnl, 2), note=""))
        units = 0.0

    for i, d in enumerate(days):
        before = (cash, units)
        wanted = positions[i]
        if wanted == 0 and units > 0:
            close_position(fills[i], d.isoformat())
        elif wanted == 1 and units == 0:
            entry_fill = execute_fill(Action.BUY, fills[i], friction, is_entry=True)
            units = cash / entry_fill
            entry_time = d.isoformat()
            volume += units * entry_fill
            cash -= units * entry_fill * (1 + friction.commission)
        # A US order fills after today's close, so mark the book held before it.
        m_cash, m_units = before if (target == "US" and i + 1 < n) else (cash, units)
        exposed += m_units > 0
        equity.append(EquityPoint(t=d.isoformat(), v=round(m_cash + m_units * closes[i], 2)))

    if units > 0:
        close_position(closes[-1], days[-1].isoformat())
        equity[-1] = EquityPoint(t=days[-1].isoformat(), v=round(cash, 2))

    return compute_full_metrics(trades, equity, n, exposed, volume, initial_capital)
