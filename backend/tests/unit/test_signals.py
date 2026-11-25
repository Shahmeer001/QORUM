"""
Unit tests for MACD, Bollinger Bands, and rule sets R1-R5.
All fixtures are synthetic; no real market data is used.
"""
from __future__ import annotations

import pytest
from app.signals.macd import _ema, calculate_macd, macd_crossover
from app.signals.bollinger import calculate_bollinger, bollinger_signal
from app.signals.rule_sets import evaluate_rule_set


# ---------------------------------------------------------------------------
# EMA helper
# ---------------------------------------------------------------------------

def test_ema_constant_series_equals_constant():
    """EMA of a constant series must equal that constant."""
    series = [100.0] * 20
    ema = _ema(series, 12)
    assert ema[-1] == pytest.approx(100.0, rel=1e-6)


def test_ema_rising_series_lags_price():
    """On a strictly rising series, EMA[-1] must be below the latest price."""
    series = list(range(1, 31))   # 1,2,...,30
    ema = _ema(series, 12)
    assert ema[-1] < series[-1]


# ---------------------------------------------------------------------------
# MACD
# ---------------------------------------------------------------------------

def test_macd_returns_zero_on_insufficient_data():
    """calculate_macd returns (0,0,0) when fewer than slow+signal bars available."""
    macd, sig, hist = calculate_macd([100.0] * 10)   # need ≥35 (26+9)
    assert macd == 0.0 and sig == 0.0 and hist == 0.0


def test_macd_rising_series_positive_macd_line():
    """On a strongly rising series the fast EMA > slow EMA → positive MACD line."""
    closes = [100.0 + i * 0.5 for i in range(60)]
    macd, sig, hist = calculate_macd(closes)
    assert macd > 0


def test_macd_falling_series_negative_macd_line():
    """On a strongly falling series the MACD line is negative."""
    closes = [200.0 - i * 0.5 for i in range(60)]
    macd, sig, hist = calculate_macd(closes)
    assert macd < 0


def test_macd_crossover_needs_enough_bars():
    """macd_crossover returns 'none' with insufficient history."""
    assert macd_crossover([100.0] * 10) == "none"


def test_macd_crossover_detects_bullish_state():
    """Fast-rising price should produce a bullish MACD state."""
    flat = [100.0] * 30
    rising = [100.0 + i * 1.5 for i in range(30)]
    closes = flat + rising
    result = macd_crossover(closes)
    assert result == "bullish"


def test_macd_crossover_detects_bearish_state():
    """Fast-falling price should produce a bearish MACD state."""
    flat = [200.0] * 30
    falling = [200.0 - i * 1.5 for i in range(30)]
    closes = flat + falling
    result = macd_crossover(closes)
    assert result == "bearish"


# ---------------------------------------------------------------------------
# Bollinger Bands
# ---------------------------------------------------------------------------

def test_bollinger_returns_zero_on_insufficient_data():
    """Returns (0,0,0) when fewer than period (20) bars available."""
    upper, mid, lower = calculate_bollinger([100.0] * 10)
    assert upper == 0.0 and mid == 0.0 and lower == 0.0


def test_bollinger_middle_band_is_sma():
    """Middle band equals the simple moving average of the last 20 closes."""
    closes = list(range(1, 31))   # 1..30, last 20 = 11..30
    upper, mid, lower = calculate_bollinger(closes)
    expected_sma = sum(range(11, 31)) / 20
    assert mid == pytest.approx(expected_sma, rel=1e-9)


def test_bollinger_upper_above_lower():
    """Upper band must be strictly above lower band for any realistic series."""
    closes = [100.0 + i * 0.1 for i in range(25)]
    upper, mid, lower = calculate_bollinger(closes)
    assert upper > mid > lower


def test_bollinger_signal_buy_when_close_at_lower_band():
    """A close exactly at the lower band should produce a BUY signal."""
    closes = [100.0] * 20
    # Build a low-std constant series so bands are very tight, then set last close below.
    upper, mid, lower = calculate_bollinger(closes)
    # Push close slightly below lower band
    closes_with_dip = closes[:-1] + [lower - 0.01]
    assert bollinger_signal(closes_with_dip) == "buy"


def test_bollinger_signal_sell_when_close_at_upper_band():
    """A close exactly at the upper band should produce a SELL signal."""
    closes = [100.0] * 20
    upper, mid, lower = calculate_bollinger(closes)
    closes_with_spike = closes[:-1] + [upper + 0.01]
    assert bollinger_signal(closes_with_spike) == "sell"


def test_bollinger_signal_none_inside_bands():
    """A close well inside the bands produces no signal."""
    # Gently oscillating series: std > 0 but close stays near the middle
    import math
    closes = [100.0 + math.sin(i * 0.3) for i in range(25)]
    # Confirm close is inside bands before asserting
    upper, mid, lower = calculate_bollinger(closes)
    assert lower < closes[-1] < upper, "fixture itself is outside bands"
    assert bollinger_signal(closes) == "none"


# ---------------------------------------------------------------------------
# Rule sets R1-R5
# ---------------------------------------------------------------------------

def _oversold_closes(n: int = 60) -> list:
    """Closes that drive RSI below 30 (sustained decline)."""
    return [200.0 - i * 1.0 for i in range(n)]


def _overbought_closes(n: int = 60) -> list:
    """Closes that drive RSI above 70 (sustained rise)."""
    return [100.0 + i * 1.0 for i in range(n)]


def test_r1_rsi_buy_on_oversold():
    assert evaluate_rule_set("R1", _oversold_closes()) == "BUY"


def test_r1_rsi_sell_on_overbought():
    assert evaluate_rule_set("R1", _overbought_closes()) == "SELL"


def test_r1_rsi_none_on_flat():
    assert evaluate_rule_set("R1", [100.0] * 60) == "NONE"


def test_r2_macd_buy_on_rising():
    flat = [100.0] * 30
    rising = [100.0 + i * 1.5 for i in range(30)]
    assert evaluate_rule_set("R2", flat + rising) == "BUY"


def test_r2_macd_sell_on_falling():
    flat = [200.0] * 30
    falling = [200.0 - i * 1.5 for i in range(30)]
    assert evaluate_rule_set("R2", flat + falling) == "SELL"


def test_r3_bollinger_buy_on_dip_below_lower():
    base = [100.0] * 20
    upper, mid, lower = calculate_bollinger(base)
    closes = base[:-1] + [lower - 0.01]
    assert evaluate_rule_set("R3", closes) == "BUY"


def test_r4_requires_both_signals():
    """R4 (AND) must return NONE when RSI fires but MACD does not."""
    # Oversold RSI but flat MACD (flat series → MACD ≈ 0)
    flat = [100.0] * 30
    # RSI will be ~50 on flat; force a dip only at the end for RSI
    dipping = flat + [100.0 - i * 2 for i in range(30)]
    rsi_fires = evaluate_rule_set("R1", dipping)
    macd_fires = evaluate_rule_set("R2", dipping)
    r4 = evaluate_rule_set("R4", dipping)
    # If RSI fires but MACD does not, R4 must be NONE
    if rsi_fires != "NONE" and macd_fires == "NONE":
        assert r4 == "NONE"
    # If both fire in the same direction, R4 must agree
    if rsi_fires != "NONE" and macd_fires == rsi_fires:
        assert r4 == rsi_fires


def test_r5_fires_when_either_fires():
    """R5 (OR) must return a direction whenever at least one signal fires."""
    # Strongly rising: both RSI overbought and MACD bullish
    closes = _overbought_closes(60)
    r5 = evaluate_rule_set("R5", closes)
    assert r5 in ("BUY", "SELL")


def test_r5_none_when_neither_fires():
    """R5 must return NONE when neither RSI nor MACD fires."""
    # Flat series → RSI≈50 (NONE), MACD≈0 (NONE)
    assert evaluate_rule_set("R5", [100.0] * 60) == "NONE"


def test_invalid_rule_raises():
    with pytest.raises(ValueError):
        evaluate_rule_set("R99", [100.0] * 60)
