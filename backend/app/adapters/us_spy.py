"""
US Equities & SPY/GLD Market Data Adapter.
"""
from __future__ import annotations

from typing import List
from app.adapters.base import MarketDataAdapter
from app.adapters.synthetic import SyntheticAdapter
from app.domain.models import Candle


class USMarketAdapter(MarketDataAdapter):
    def __init__(self, scenario: str = "neutral") -> None:
        self.scenario = scenario

    def get_candles(self, symbol: str = "SPY", limit: int = 100) -> List[Candle]:
        base = 580.0 if "SPY" in symbol else 260.0 if "GLD" in symbol else 200.0
        return SyntheticAdapter(scenario=self.scenario, base_price=base).get_candles(symbol, limit)

    def get_latest(self, symbol: str = "SPY") -> Candle:
        return self.get_candles(symbol, limit=1)[-1]
