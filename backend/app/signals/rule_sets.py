"""
Rule sets R1-R5, defined on top of RSI, MACD, and Bollinger Bands.

R1: RSI            — RSI < 30 → BUY; RSI > 70 → SELL
R2: MACD           — signal-line crossover: bullish cross → BUY, bearish cross → SELL
R3: Bollinger      — close <= lower band → BUY; close >= upper band → SELL
R4: RSI AND MACD   — both must agree on the direction (RSI zone + MACD crossover)
R5: RSI OR MACD    — either fires (agreement preferred when both fire)

Each evaluate() returns one of: "BUY", "SELL", "NONE" for a given close series.
Parameters (RSI thresholds, MACD periods, Bollinger period/std) live in settings.py.
"""
from __future__ import annotations

from typing import Sequence

from app.config.settings import RSI_BUY_THRESHOLD, RSI_SELL_THRESHOLD
from app.signals.bollinger import bollinger_signal
from app.signals.macd import macd_crossover
from app.signals.rsi import calculate_rsi


def rsi_signal(closes: Sequence[float]) -> str:
    rsi = calculate_rsi(closes)
    if rsi < RSI_BUY_THRESHOLD:
        return "BUY"
    if rsi > RSI_SELL_THRESHOLD:
        return "SELL"
    return "NONE"


def macd_signal(closes: Sequence[float]) -> str:
    state = macd_crossover(closes)
    if state == "bullish":
        return "BUY"
    if state == "bearish":
        return "SELL"
    return "NONE"


def evaluate_rule_set(rule_id: str, closes: Sequence[float]) -> str:
    """Evaluate a named rule set R1-R5 on the latest close series."""
    if rule_id == "R1":
        return rsi_signal(closes)
    if rule_id == "R2":
        return macd_signal(closes)
    if rule_id == "R3":
        s = bollinger_signal(closes)
        return s.upper() if s in ("buy", "sell") else "NONE"
    if rule_id == "R4":  # RSI AND MACD
        r = rsi_signal(closes)
        m = macd_signal(closes)
        if r == m and r != "NONE":
            return r
        return "NONE"
    if rule_id == "R5":  # RSI OR MACD
        r = rsi_signal(closes)
        m = macd_signal(closes)
        if r == m:
            return r  # both agree (including both NONE)
        if r != "NONE":
            return r
        if m != "NONE":
            return m
        return "NONE"
    raise ValueError(f"Unknown rule set: {rule_id}")
