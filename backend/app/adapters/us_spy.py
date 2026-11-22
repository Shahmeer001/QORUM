"""
US Equities & SPY Market Data Adapter.
Reads real daily candlestick data from cache (backend/data_cache/spy_daily.csv).
Strictly parses day-first ("DD/MM/YYYY HH:MM:SS"), ignores time of day,
and enforces NYSE weekend and holiday closures.
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Set
from dateutil import parser
import pandas as pd

from app.adapters.base import MarketDataAdapter
from app.config.settings import DATA_CACHE_DIR
from app.domain.models import Candle


class USMarketAdapter(MarketDataAdapter):
    def __init__(
        self,
        csv_path: Optional[Path] = None,
        scenario: str = "neutral",
        current_date: Optional[str] = None,
    ) -> None:
        self.scenario = scenario
        self.csv_path = csv_path or (DATA_CACHE_DIR / "spy_daily.csv")
        self.current_date = current_date
        self._df: Optional[pd.DataFrame] = None
        self._trading_dates: Optional[Set[date]] = None

    def _load_data(self) -> None:
        if self._df is not None:
            return

        if not self.csv_path.exists():
            raise FileNotFoundError(f"SPY daily dataset not found at {self.csv_path}")

        df = pd.read_csv(self.csv_path)
        # Parse day-first, use date only
        df["parsed_date"] = pd.to_datetime(
            df["Date"].astype(str).str.split().str[0], format="%d/%m/%Y"
        ).dt.date
        df = df.sort_values("parsed_date").reset_index(drop=True)

        self._df = df
        self._trading_dates = set(df["parsed_date"])

    def get_candles(
        self, symbol: str = "SPY", limit: int = 100, date_str: str | None = None
    ) -> List[Candle]:
        self._load_data()
        effective_date_str = date_str or self.current_date

        if effective_date_str is not None:
            dt = parser.parse(effective_date_str).date() if "-" in effective_date_str else datetime.strptime(effective_date_str, "%d/%m/%Y").date()
            # If weekend (Saturday=5, Sunday=6) or holiday (not in trading dates), market is closed -> 0 candles
            if dt.weekday() in (5, 6) or dt not in self._trading_dates:
                return []

            filtered_df = self._df[self._df["parsed_date"] <= dt]
        else:
            filtered_df = self._df

        subset = filtered_df.tail(limit)
        return [
            Candle(
                timestamp=f"{row['parsed_date'].isoformat()} 16:00:00-05:00",
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
                quote_volume=0.0,
            )
            for _, row in subset.iterrows()
        ]

    def get_latest(self, symbol: str = "SPY") -> Candle:
        candles = self.get_candles(symbol, limit=1)
        return candles[-1] if candles else Candle(timestamp="", open=0, high=0, low=0, close=0, volume=0)
