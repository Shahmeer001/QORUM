from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from app.domain.models import Candle


class MarketDataAdapter(ABC):
    """Abstract data adapter interface for retrieving market candle bars."""

    @abstractmethod
    def get_candles(self, symbol: str, limit: int = 100) -> List[Candle]:
        """Fetch historical candle series."""
        pass

    @abstractmethod
    def get_latest(self, symbol: str) -> Candle:
        """Fetch the most recent closed candle."""
        pass
