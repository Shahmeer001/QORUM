"""
US Equities & SPY/GLD Market Data Adapter.
Handles weekend market closures (Saturday/Sunday: NYSE/NASDAQ closed -> no new candle).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from dateutil import parser

from app.adapters.base import MarketDataAdapter
from app.adapters.synthetic import SyntheticAdapter
from app.domain.models import Candle


class USMarketAdapter(MarketDataAdapter):
    def __init__(self, scenario: str = "neutral") -> None:
        self.scenario = scenario

    def get_candles(self, symbol: str = "SPY", limit: int = 100, date_str: str | None = None) -> List[Candle]:
        # If date is a weekend (Saturday=5, Sunday=6), US markets are closed -> no new candles
        if date_str is not None:
            dt = parser.parse(date_str)
            if dt.weekday() in (5, 6):
                return []

        base = 580.0 if "SPY" in symbol else 260.0 if "GLD" in symbol else 200.0
        return SyntheticAdapter(scenario=self.scenario, base_price=base).get_candles(symbol, limit)

    def get_latest(self, symbol: str = "SPY") -> Candle:
        candles = self.get_candles(symbol, limit=1)
        return candles[-1] if candles else Candle(timestamp="", open=0, high=0, low=0, close=0, volume=0)
