"""
Market Volatility Signal.
Computes annualized or periodic realized volatility and ATR % from candles.
"""
from __future__ import annotations

from typing import List, Sequence
import numpy as np
import pandas as pd


def calculate_realized_volatility(closes: Sequence[float], window: int = 14) -> float:
    """
    Calculates percentage standard deviation of log returns across `window` candles.
    Expressed in percentage points (e.g., 2.5 means 2.5%).
    """
    if len(closes) < 3:
        return 1.0
    c = np.array(closes, dtype=float)
    returns = np.diff(np.log(c))
    recent = returns[-window:] if len(returns) >= window else returns
    vol = float(np.std(recent, ddof=1) * 100.0) if len(recent) > 1 else 1.0
    return round(vol, 2)
