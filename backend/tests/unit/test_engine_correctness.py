"""
Engine Correctness Verification Tests for WP4 Engine.
Enforces:
(a) Always-long equals buy-and-hold minus one round-trip of friction
(b) Always-flat returns exactly 0.0 PnL and 0.0 Drawdown
(c) Perfect-foresight oracle produces a strongly positive result
(d) Sign of a short verified with a hand-built falling series
"""
from __future__ import annotations

import pytest
from app.domain.enums import Action
from app.domain.models import Candle
from app.simulator.metrics import compute_full_metrics
from app.simulator.trade_engine import (
    MarketFriction,
    calculate_trade_pnl,
    execute_fill,
    simulate_trades,
)


def test_engine_always_long_equals_buy_and_hold_with_roundtrip_friction():
    """
    (a) Always-long must equal buy-and-hold minus one round-trip of friction.
    """
    friction = MarketFriction(commission=0.0005, slippage=0.0002)
    initial_capital = 10000.0

    candles = [
        Candle(timestamp="2026-01-01", open=100.0, high=102.0, low=99.0, close=101.0, volume=1000),
        Candle(timestamp="2026-01-02", open=101.0, high=105.0, low=100.0, close=104.0, volume=1000),
        Candle(timestamp="2026-01-03", open=104.0, high=112.0, low=103.0, close=110.0, volume=1000),
    ]

    # Theoretical Buy & Hold with friction:
    entry_fill = execute_fill(Action.BUY, candles[0].open, friction, is_entry=True)
    exit_fill = execute_fill(Action.BUY, candles[-1].close, friction, is_entry=False)
    units = initial_capital / entry_fill
    expected_net_pnl, expected_comm, expected_gross = calculate_trade_pnl(entry_fill, exit_fill, units, friction)

    trades, equity = simulate_trades(Action.BUY, "US", candles, initial_capital=initial_capital)

    assert len(trades) == 1
    assert trades[0].pnl == pytest.approx(expected_net_pnl, abs=0.01)
    assert equity[-1].v == pytest.approx(initial_capital + expected_net_pnl, abs=0.01)


def test_engine_always_flat_returns_zero():
    """
    (b) Always-flat returns exactly 0 PnL, 0 Drawdown, 0 Trades.
    """
    candles = [
        Candle(timestamp=f"2026-01-0{i+1}", open=100.0 + i * 10, high=115.0 + i * 10, low=95.0, close=105.0 + i * 10, volume=1000)
        for i in range(5)
    ]
    # Stance is HOLD -> flat
    trades, equity = simulate_trades(Action.HOLD, "US", candles, initial_capital=10000.0)

    assert len(trades) == 0
    assert all(pt.v == 10000.0 for pt in equity)

    perf = compute_full_metrics(trades, equity, total_days=5, days_exposed=0, total_volume_traded=0, initial_capital=10000.0)
    assert perf.pnl_dollars == 0.0
    assert perf.pnl_pct == 0.0
    assert perf.max_drawdown_pct == 0.0
    assert perf.trade_count == 0
    assert perf.turnover == 0.0


def test_engine_perfect_foresight_oracle_strongly_positive():
    """
    (c) A perfect-foresight oracle must produce a strongly positive result.
    """
    friction = MarketFriction(commission=0.0005, slippage=0.0002)
    initial_capital = 10000.0

    # 4 periods alternating: rise, fall, rise
    # Prices: 100 -> 120 -> 90 -> 130
    prices = [100.0, 120.0, 90.0, 130.0]

    # Oracle buys before rise, shorts before fall, buys before rise
    # Trade 1: Long 100 -> 120 (+20%)
    e1 = execute_fill(Action.BUY, prices[0], friction, is_entry=True)
    x1 = execute_fill(Action.BUY, prices[1], friction, is_entry=False)
    pnl1, _, _ = calculate_trade_pnl(e1, x1, initial_capital / e1, friction, is_short=False)

    # Trade 2: Short 120 -> 90 (+25% on drop)
    cap2 = initial_capital + pnl1
    e2 = execute_fill(Action.SELL, prices[1], friction, is_entry=True, is_short=True)
    x2 = execute_fill(Action.SELL, prices[2], friction, is_entry=False, is_short=True)
    pnl2, _, _ = calculate_trade_pnl(e2, x2, cap2 / e2, friction, is_short=True)

    # Trade 3: Long 90 -> 130 (+44% on rise)
    cap3 = cap2 + pnl2
    e3 = execute_fill(Action.BUY, prices[2], friction, is_entry=True)
    x3 = execute_fill(Action.BUY, prices[3], friction, is_entry=False)
    pnl3, _, _ = calculate_trade_pnl(e3, x3, cap3 / e3, friction, is_short=False)

    total_oracle_pnl = pnl1 + pnl2 + pnl3
    oracle_return_pct = (total_oracle_pnl / initial_capital) * 100

    assert oracle_return_pct > 80.0, f"Oracle should be strongly positive, got {oracle_return_pct:.2f}%"
    assert pnl1 > 0
    assert pnl2 > 0
    assert pnl3 > 0


def test_engine_short_sign_verified_on_falling_series():
    """
    (d) The sign of a short must be verified with a hand-built falling series.
    A short trade on a falling price series MUST yield a strictly positive return.
    """
    friction = MarketFriction(commission=0.0005, slippage=0.0002)
    initial_capital = 10000.0

    raw_entry = 100.0
    raw_exit = 80.0  # 20% drop

    # Short entry: receives lower price with slippage
    entry_fill = execute_fill(Action.SELL, raw_entry, friction, is_entry=True, is_short=True)
    assert entry_fill == pytest.approx(100.0 * (1 - 0.0002), rel=1e-6)

    # Short exit: pays higher price with slippage
    exit_fill = execute_fill(Action.SELL, raw_exit, friction, is_entry=False, is_short=True)
    assert exit_fill == pytest.approx(80.0 * (1 + 0.0002), rel=1e-6)

    units = initial_capital / entry_fill
    net_pnl, total_comm, gross = calculate_trade_pnl(entry_fill, exit_fill, units, friction, is_short=True)

    # Gross should be units * (100 - 80) > 0
    assert gross > 0
    assert net_pnl > 0, f"Shorting a falling series must yield positive net PnL, got {net_pnl}"
    assert net_pnl == pytest.approx(units * (entry_fill - exit_fill) - total_comm, rel=1e-6)

    # Compare with a long trade on the same falling series (which MUST be negative)
    long_e = execute_fill(Action.BUY, raw_entry, friction, is_entry=True, is_short=False)
    long_x = execute_fill(Action.BUY, raw_exit, friction, is_entry=False, is_short=False)
    long_pnl, _, long_gross = calculate_trade_pnl(long_e, long_x, units, friction, is_short=False)

    assert long_pnl < 0
    assert net_pnl * long_pnl < 0, "Short and Long on a falling series must have opposite signs!"
