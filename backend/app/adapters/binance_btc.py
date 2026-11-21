"""
Binance BTC Market Data Adapter.
Reads cached historical snapshot or research OHLCV data.
"""
from __future__ import annotations

from pathlib import Path
from typing import List
import pandas as pd

from app.adapters.base import MarketDataAdapter
from app.domain.models import Candle


class BinanceBTCAdapter(MarketDataAdapter):
    def __init__(self, csv_path: Path | None = None) -> None:
        if csv_path is None:
            # Fall back to research output if available
            root = Path(__file__).resolve().parent.parent.parent.parent
            self.csv_path = root / "research" / "output" / "btc_ohlcv.csv"
        else:
            self.csv_path = csv_path

    def get_candles(self, symbol: str = "BTCUSDT", limit: int = 100) -> List[Candle]:
        if self.csv_path.exists():
            df = pd.read_csv(self.csv_path).tail(limit)
            return [
                Candle(
                    timestamp=str(row["timestamp"]),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row["Volume"]),
                    quote_volume=float(row.get("QuoteVolume", 0.0)),
                )
                for _, row in df.iterrows()
            ]

        # Deterministic fallback when CSV hasn't been generated yet
        from app.adapters.synthetic import SyntheticAdapter
        return SyntheticAdapter(scenario="bull", base_price=88000.0).get_candles(symbol, limit)

    def get_latest(self, symbol: str = "BTCUSDT") -> Candle:
        return self.get_candles(symbol, limit=1)[-1]
