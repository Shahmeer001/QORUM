"""
Deterministic Synthetic Market Data Adapter.
Produces repeatable Bull, Bear, and Neutral candle sequences for testing and offline simulations.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List
import numpy as np

from app.adapters.base import MarketDataAdapter
from app.domain.models import Candle


class SyntheticAdapter(MarketDataAdapter):
    def __init__(self, scenario: str = "bull", base_price: float = 2000.0, current_date: str | None = None) -> None:
        self.scenario = scenario.lower()
        self.base_price = base_price
        # Accepted for interface parity with the real adapters. Synthetic data is
        # generated on demand (FYP2/inactive markets), so there is no real future
        # to deny; the attribute is stored but does not filter the generated series.
        self.current_date = current_date

    def get_candles(self, symbol: str = "XAUUSD", limit: int = 100, date_str: str | None = None) -> List[Candle]:
        now = datetime(2026, 11, 10, 19, 0, 0, tzinfo=timezone.utc)
        candles: List[Candle] = []

        price = self.base_price
        if self.scenario == "bull":
            np.random.seed(42)
            drift = 0.0015       # upward trend
            volatility = 0.002   # low volatility (~0.2% - 1.0%), safe for risk layer
        elif self.scenario == "bear":
            np.random.seed(1337)
            drift = -0.0040      # steep breakdown
            volatility = 0.038   # high volatility (> 3.5%), exceeds 2.5% max_vol
        else:
            np.random.seed(777)
            drift = 0.0001       # neutral consolidation
            volatility = 0.005

        for i in range(limit, 0, -1):
            t = (now - timedelta(minutes=5 * i)).isoformat()
            ret = drift + np.random.normal(0, volatility)
            open_p = price
            close_p = max(10.0, open_p * (1.0 + ret))
            high_p = max(open_p, close_p) * (1.0 + abs(np.random.normal(0, volatility * 0.4)))
            low_p = min(open_p, close_p) * (1.0 - abs(np.random.normal(0, volatility * 0.4)))
            volume = float(np.random.uniform(500, 2000))
            quote_vol = volume * close_p

            candles.append(
                Candle(
                    timestamp=t,
                    open=round(open_p, 2),
                    high=round(high_p, 2),
                    low=round(low_p, 2),
                    close=round(close_p, 2),
                    volume=round(volume, 2),
                    quote_volume=round(quote_vol, 2),
                )
            )
            price = close_p

        return candles

    def get_latest(self, symbol: str = "XAUUSD") -> Candle:
        candles = self.get_candles(symbol=symbol, limit=1)
        return candles[-1]
