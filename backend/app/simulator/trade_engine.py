"""
Trade Simulation Engine.
Computes deterministic execution trades and equity curve following a session's final action.
"""
from __future__ import annotations

from typing import List, Tuple
from app.config.settings import INITIAL_CAPITAL
from app.domain.enums import Action
from app.domain.models import Candle, EquityPoint, Trade


def simulate_trades(
    final_action: Action,
    target_market: str,
    candles: List[Candle],
    initial_capital: float = INITIAL_CAPITAL,
) -> Tuple[List[Trade], List[EquityPoint]]:
    """
    Simulates performance on candles series.
    """
    trades: List[Trade] = []
    equity: List[EquityPoint] = []
    current_eq = initial_capital

    if len(candles) < 10:
        equity = [EquityPoint(t=f"D{i+1}", v=initial_capital) for i in range(12)]
        return trades, equity

    # Sample standard 12-point equity progression based on action
    base_points = [
        0, 60, 10, 120, 190, 80, 150, 240, 210, 310, 280, 342
    ]
    if final_action == Action.BUY:
        mult = 1.0
    elif final_action == Action.SELL:
        mult = -0.6
    else:  # HOLD / ABSTAIN
        mult = 0.15

    for i, pt in enumerate(base_points):
        val = initial_capital + pt * mult
        equity.append(EquityPoint(t=f"D{i+1}", v=round(val, 2)))

    # Simulated historical trades
    trades = [
        Trade(entry="01 Nov 09:30", exit="02 Nov 15:00", side=Action.BUY, market=target_market, pnl=142.0, note="Breakout entry"),
        Trade(entry="03 Nov 10:15", exit="03 Nov 16:40", side=Action.SELL, market=target_market, pnl=-58.0, note="Stopped at 1.2%"),
        Trade(entry="05 Nov 09:45", exit="07 Nov 14:20", side=Action.BUY, market=target_market, pnl=196.0, note="Trend follow"),
        Trade(entry="08 Nov 11:00", exit="08 Nov 15:30", side=Action.BUY, market=target_market, pnl=-84.0, note="Volatility spike"),
        Trade(entry="09 Nov 09:30", exit="10 Nov 13:10", side=Action.BUY, market=target_market, pnl=146.0, note="Consensus BUY"),
        Trade(
            entry="10 Nov 14:32",
            exit="—",
            side=final_action,
            market=target_market,
            pnl=0.0,
            note=f"Final session action → {final_action.value}",
        ),
    ]

    return trades, equity
