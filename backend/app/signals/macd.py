"""
MACD (Moving Average Convergence Divergence), hand-written.

Standard parameters (12, 26, 9), all from config (settings.py):
  - fast EMA period   : MACD_FAST_PERIOD     = 12
  - slow EMA period   : MACD_SLOW_PERIOD     = 26
  - signal period     : MACD_SIGNAL_PERIOD   = 9

MACD line = EMA(fast) - EMA(slow)
Signal line = EMA(MACD line, signal period)
Histogram = MACD line - Signal line

A signal-line crossover is:
  - BULLISH when the MACD line crosses above the signal line
  - BEARISH when the MACD line crosses below the signal line
"""
from __future__ import annotations

from typing import List, Sequence, Tuple

from app.config.settings import MACD_FAST_PERIOD, MACD_SIGNAL_PERIOD, MACD_SLOW_PERIOD


def _ema(values: Sequence[float], period: int) -> List[float]:
    """Exponential moving average, seeded with the SMA of the first `period` values."""
    n = len(values)
    if n == 0:
        return []
    if n < period:
        # Not enough data: return the simple mean repeated (degenerate but safe).
        m = sum(values) / n
        return [m] * n

    alpha = 2.0 / (period + 1.0)
    out: List[float] = []
    # Seed with SMA of the first `period` values.
    seed = sum(values[:period]) / period
    for i in range(n):
        if i < period - 1:
            out.append(sum(values[: i + 1]) / (i + 1))  # SMA warm-up
        elif i == period - 1:
            out.append(seed)
        else:
            out.append(out[-1] + alpha * (values[i] - out[-1]))
    return out


def calculate_macd(
    closes: Sequence[float],
    fast: int = MACD_FAST_PERIOD,
    slow: int = MACD_SLOW_PERIOD,
    signal: int = MACD_SIGNAL_PERIOD,
) -> Tuple[float, float, float]:
    """
    Returns (macd_line, signal_line, histogram) at the latest bar.

    If there is insufficient history (fewer than `slow + signal` closes),
    returns (0.0, 0.0, 0.0) — no signal can be formed.
    """
    n = len(closes)
    if n < slow + signal:
        return 0.0, 0.0, 0.0

    ema_fast = _ema(closes, fast)
    ema_slow = _ema(closes, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    # Signal line: EMA of the MACD line (use the valid part, from index slow-1).
    valid_macd = macd_line[slow - 1:]
    signal_line_series = _ema(valid_macd, signal)

    macd = macd_line[-1]
    sig = signal_line_series[-1]
    return macd, sig, macd - sig


def macd_crossover(
    closes: Sequence[float],
    fast: int = MACD_FAST_PERIOD,
    slow: int = MACD_SLOW_PERIOD,
    signal: int = MACD_SIGNAL_PERIOD,
) -> str:
    """
    Returns the crossover state at the latest bar:
      "bullish"  – MACD line above signal line (recent cross up or sustained)
      "bearish"  – MACD line below signal line
      "none"     – insufficient data
    """
    n = len(closes)
    if n < slow + signal + 1:
        return "none"

    # Compute for the last two bars to detect the actual cross.
    c_prev = list(closes[:-1])
    c_curr = list(closes)

    def _state(cl):
        ema_f = _ema(cl, fast)
        ema_s = _ema(cl, slow)
        macd_series = [f - s for f, s in zip(ema_f, ema_s)]
        valid = macd_series[slow - 1:]
        sig_series = _ema(valid, signal)
        return macd_series[-1], sig_series[-1]

    m_prev, s_prev = _state(c_prev)
    m_curr, s_curr = _state(c_curr)

    if m_curr > s_curr and m_prev <= s_prev:
        return "bullish"  # fresh cross up
    if m_curr < s_curr and m_prev >= s_prev:
        return "bearish"  # fresh cross down
    # No fresh cross: report the standing relationship as state.
    if m_curr > s_curr:
        return "bullish"
    if m_curr < s_curr:
        return "bearish"
    return "none"
