"""
Temporal guard tests (Part 0.4).

Rules enforced:
- A real adapter built without a decision date returns NO candles (default-deny),
  so no code path can leak bars that close after the intended cutoff.
- A session run on a past decision date cannot see bars that close after that date.
"""
from __future__ import annotations

from app.adapters.binance_btc import BinanceBTCAdapter
from app.adapters.us_spy import USMarketAdapter


def test_real_adapters_deny_all_without_a_decision_date():
    """Default-deny: with no current_date and no date_str, both real adapters return []."""
    us = USMarketAdapter()
    btc = BinanceBTCAdapter()
    assert us.get_candles(symbol="SPY", limit=50) == []
    assert btc.get_candles(symbol="BTCUSDT", limit=50) == []


def test_current_date_attribute_also_enforces_cutoff():
    """Setting current_date (as the orchestrator does) is equivalent to date_str."""
    us = USMarketAdapter(current_date="2026-11-20")
    btc = BinanceBTCAdapter(current_date="2026-11-20")
    assert len(us.get_candles(symbol="SPY", limit=50)) == 50
    assert len(btc.get_candles(symbol="BTCUSDT", limit=24)) == 24


def test_session_on_past_date_cannot_see_later_bars():
    """
    A session run with an earlier decision date must NOT include bars that close
    after that date. The past cutoff returns strictly fewer candles and its last
    bar predates the final dataset bar.
    """
    adapter = USMarketAdapter()
    past = adapter.get_candles(symbol="SPY", date_str="2025-06-16", limit=10000)
    full = adapter.get_candles(symbol="SPY", date_str="2026-11-20", limit=10000)

    # 1. The past cutoff exposes strictly fewer candles than the full window.
    assert len(full) > len(past)

    # 2. The past cutoff's last bar is on or before the past decision date.
    assert past[-1].timestamp.split()[0] <= "2025-06-16"

    # 3. The full window's last bar is the final dataset trading day.
    assert full[-1].timestamp.split()[0] == "2026-11-20"

    # 4. The past cutoff never exposes the final dataset bar (no look-ahead).
    assert all("2026-11-20" not in c.timestamp for c in past[-3:])


def test_btc_past_date_excludes_future_hourly_bars():
    """The BTC adapter honours the past decision-date cutoff at hourly granularity."""
    adapter = BinanceBTCAdapter()
    # Default limit=100 is enough: we compare the LAST candle returned under each cutoff.
    past = adapter.get_candles(symbol="BTCUSDT", date_str="2025-06-16")
    full = adapter.get_candles(symbol="BTCUSDT", date_str="2026-11-20")

    # 1. The past cutoff's last bar closes on the past decision date (2025-06-16
    #    is summer/EDT, so the US close is 20:00 UTC).
    assert past[-1].timestamp.startswith("2025-06-16")

    # 2. The full window's last bar is the final dataset candle (2026-11-20 21:00 UTC).
    assert full[-1].timestamp == "2026-11-20 21:00:00+00:00"

    # 3. The past cutoff never exposes the final dataset bar (no look-ahead).
    assert all("2026-11-20" not in c.timestamp for c in past)
