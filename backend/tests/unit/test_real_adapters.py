"""
Unit tests for WP3: Real market data adapters and dynamic registry loader.
Covers SPY daily CSV, Binance BTC 1h close-time boundary at US close cutoff,
weekend/holiday closures, and dynamic loader contracts.
"""
from datetime import datetime, timezone
import pytest

from app.adapters.binance_btc import BinanceBTCAdapter
from app.adapters.synthetic import SyntheticAdapter
from app.adapters.us_spy import USMarketAdapter
from app.config.settings import get_us_close_utc
from app.modes.runner import get_adapter_for_market, load_markets_config


def test_us_market_adapter_loads_real_spy_data():
    """USMarketAdapter loads real daily data from spy_daily.csv and parses day-first."""
    adapter = USMarketAdapter()
    candles = adapter.get_candles(symbol="SPY", limit=50, date_str="2026-11-20")

    assert len(candles) == 50
    # Spot-check realistic SPY price range
    assert 300.0 < candles[-1].close < 1000.0
    assert candles[-1].open > 0.0
    assert candles[-1].volume > 0.0


def test_us_market_adapter_weekend_and_holiday_closures():
    """US market returns 0 candles on weekends and official NYSE holidays."""
    adapter = USMarketAdapter()

    # Saturday 2026-11-14 -> Weekend closed
    assert len(adapter.get_candles(date_str="2026-11-14")) == 0
    # Sunday 2026-11-15 -> Weekend closed
    assert len(adapter.get_candles(date_str="2026-11-15")) == 0

    # Monday 2026-11-16 -> Normal trading day
    monday_candles = adapter.get_candles(date_str="2026-11-16", limit=10)
    assert len(monday_candles) > 0
    assert "2026-11-16" in monday_candles[-1].timestamp

    # Independence Day observed (Friday 2026-07-03) -> Holiday closed
    assert len(adapter.get_candles(date_str="2026-07-03")) == 0


def test_binance_btc_adapter_loads_real_hourly_data():
    """BinanceBTCAdapter loads real 1h candles from btc_1h.csv with close time = open + 1h."""
    adapter = BinanceBTCAdapter()
    candles = adapter.get_candles(symbol="BTCUSDT", limit=24, date_str="2026-11-20")

    assert len(candles) == 24
    # Realistic Bitcoin prices in 2022-2026
    assert 15000.0 < candles[-1].close < 200000.0
    assert candles[-1].volume > 0.0


def test_binance_btc_cutoff_boundary_at_us_close():
    """
    WP3 Boundary Requirement:
    Binance timestamps are open times: close time = open + 1h.
    On 2026-11-20, US Close is 4:00 PM EST (21:00 UTC in winter).
    Only candles closed at or before 21:00 UTC must be included:
      - Candle opening 20:00 UTC (closing 21:00 UTC) must be INCLUDED as the last candle.
      - Candle opening 21:00 UTC (closing 22:00 UTC) must be EXCLUDED.
    """
    adapter = BinanceBTCAdapter()
    cutoff_utc = get_us_close_utc("2026-11-20")

    # Verify cutoff is exactly 21:00:00 UTC
    assert cutoff_utc == datetime(2026, 11, 20, 21, 0, 0, tzinfo=timezone.utc)

    # Fetch candles ending at this cutoff
    candles = adapter.get_candles(symbol="BTCUSDT", limit=50, date_str="2026-11-20")
    last_candle = candles[-1]

    # The last candle timestamp is its close time, which must match the exact cutoff (21:00 UTC)
    assert last_candle.timestamp == "2026-11-20 21:00:00+00:00"

    # Confirm by inspecting raw data that the 21:00-opening candle (closing 22:00) is NOT in candles
    candle_timestamps = [c.timestamp for c in candles]
    assert "2026-11-20 22:00:00+00:00" not in candle_timestamps
    assert "2026-11-20 23:00:00+00:00" not in candle_timestamps


def test_dynamic_registry_loader_active_vs_inactive():
    """
    Registry loader verifies:
    - Active markets (US, CRYPTO) strictly use real adapters, never synthetic.
    - Inactive markets (PSX, FOREX, GOLD) load dynamic adapter class (tagged FYP2).
    """
    cfg = load_markets_config()

    # Active markets
    us_adapter = get_adapter_for_market("US", cfg.get("US", {}))
    assert isinstance(us_adapter, USMarketAdapter)
    assert not isinstance(us_adapter, SyntheticAdapter)

    crypto_adapter = get_adapter_for_market("CRYPTO", cfg.get("CRYPTO", {}))
    assert isinstance(crypto_adapter, BinanceBTCAdapter)
    assert not isinstance(crypto_adapter, SyntheticAdapter)

    # Inactive markets
    gold_adapter = get_adapter_for_market("GOLD", cfg.get("GOLD", {}))
    assert isinstance(gold_adapter, SyntheticAdapter)
    assert cfg["GOLD"]["phase"] == "FYP2"
    assert cfg["GOLD"]["active"] is False

    psx_adapter = get_adapter_for_market("PSX", cfg.get("PSX", {}))
    assert isinstance(psx_adapter, SyntheticAdapter)
    assert cfg["PSX"]["phase"] == "FYP2"
    assert cfg["PSX"]["active"] is False
