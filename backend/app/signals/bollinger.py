"""
Bollinger Bands, hand-written.

Standard parameters (20, 2 std), all from config (settings.py):
  - period         : BOLLINGER_PERIOD  = 20
  - std multiplier : BOLLINGER_NSTD    = 2.0

Middle band = simple moving average of the last `period` closes.
Upper band  = SMA + nstd * rolling std (ddof=1 / sample std).
Lower band  = SMA - nstd * rolling std.

Signal at the latest bar:
  - close <= lower band → potential BUY (oversold, price touched lower band).
  - close >= upper band → potential SELL (overbought, price touched upper band).
  - otherwise           → no signal.
"""
from __future__ import annotations

from math import sqrt
from typing import Sequence, Tuple

from app.config.settings import BOLLINGER_NSTD, BOLLINGER_PERIOD


def calculate_bollinger(
    closes: Sequence[float],
    period: int = BOLLINGER_PERIOD,
    nstd: float = BOLLINGER_NSTD,
) -> Tuple[float, float, float]:
    """
    Returns (upper_band, middle_band, lower_band) at the latest bar.
    If fewer than `period` closes are available, returns (0.0, 0.0, 0.0).
    """
    n = len(closes)
    if n < period:
        return 0.0, 0.0, 0.0

    window = list(closes[-period:])
    sma = sum(window) / period
    variance = sum((x - sma) ** 2 for x in window) / (period - 1)  # sample std (ddof=1)
    std = sqrt(variance)
    return sma + nstd * std, sma, sma - nstd * std


def bollinger_signal(
    closes: Sequence[float],
    period: int = BOLLINGER_PERIOD,
    nstd: float = BOLLINGER_NSTD,
) -> str:
    """
    Returns the Bollinger signal at the latest close:
      "buy"   – close <= lower band
      "sell"  – close >= upper band
      "none"  – inside the bands (no signal)
      "none"  – insufficient data
    """
    if len(closes) < period:
        return "none"

    upper, middle, lower = calculate_bollinger(closes, period, nstd)
    latest = closes[-1]

    if latest <= lower:
        return "buy"
    if latest >= upper:
        return "sell"
    return "none"
