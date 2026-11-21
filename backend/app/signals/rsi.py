"""
RSI (Relative Strength Index) Calculation.
Must match the exact exponential weighted formula in research/03_roi_and_indicators.py.
"""
from __future__ import annotations

from typing import List, Sequence
import numpy as np
import pandas as pd

from app.config.settings import RSI_PERIOD


def calculate_rsi(closes: Sequence[float], period: int = RSI_PERIOD) -> float:
    """
    Computes current RSI from a sequence of closes.
    Uses exact EWM formula with alpha = 1 / period and adjust=False.
    """
    if len(closes) < period + 1:
        return 50.0  # neutral fallback if insufficient lookback

    s = pd.Series(closes, dtype=float)
    delta = s.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    denom = avg_loss.iloc[-1]
    if denom == 0.0 or np.isnan(denom):
        return 100.0 if avg_gain.iloc[-1] > 0 else 50.0

    rs = avg_gain.iloc[-1] / denom
    rsi = 100.0 - 100.0 / (1.0 + rs)
    return float(np.clip(rsi, 0.0, 100.0))
