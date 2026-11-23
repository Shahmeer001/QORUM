"""
Binance BTC Market Data Adapter.
Reads real 1-hour candlestick data from cache (backend/data_cache/btc_1h.csv).
Binance timestamps are OPEN times in UTC.
Enforces close time = open + 1h, and strictly filters candles closed
at or before the US close cutoff (e.g. 21:00 UTC on 2026-11-20 in winter).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional
import pandas as pd

from app.adapters.base import MarketDataAdapter
from app.config.settings import DATA_CACHE_DIR, get_us_close_utc
from app.domain.models import Candle


class BinanceBTCAdapter(MarketDataAdapter):
    def __init__(
        self, csv_path: Optional[Path] = None, current_date: Optional[str] = None
    ) -> None:
        self.csv_path = csv_path or (DATA_CACHE_DIR / "btc_1h.csv")
        self.current_date = current_date
        self._df: Optional[pd.DataFrame] = None

    def _load_data(self) -> None:
        if self._df is not None:
            return

        if not self.csv_path.exists():
            raise FileNotFoundError(f"BTC 1h dataset not found at {self.csv_path}")

        df = pd.read_csv(self.csv_path)
        # Parse open time and compute close time (open + 1h)
        df["open_dt"] = pd.to_datetime(df["timestamp"])
        df["close_dt"] = df["open_dt"] + pd.Timedelta(hours=1)
        df = df.sort_values("open_dt").reset_index(drop=True)
        self._df = df

    def get_candles(
        self, symbol: str = "BTCUSDT", limit: int = 100, date_str: str | None = None
    ) -> List[Candle]:
        self._load_data()
        effective_date_str = date_str or self.current_date

        # Temporal guard (default-deny): a decision date is mandatory. Without
        # one the adapter returns NO candles, so no code path can leak bars
        # that close after the intended cutoff. Callers must set `current_date`
        # (per session) or pass `date_str` explicitly.
        if effective_date_str is None:
            return []

        cutoff = get_us_close_utc(effective_date_str)
        filtered_df = self._df[self._df["close_dt"] <= cutoff]
        subset = filtered_df.tail(limit)
        return [
            Candle(
                timestamp=row["close_dt"].strftime("%Y-%m-%d %H:%M:%S+00:00"),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
                quote_volume=float(row.get("QuoteVolume", 0.0)),
            )
            for _, row in subset.iterrows()
        ]

    def get_latest(self, symbol: str = "BTCUSDT") -> Candle:
        candles = self.get_candles(symbol, limit=1)
        return candles[-1] if candles else Candle(timestamp="", open=0, high=0, low=0, close=0, volume=0)
