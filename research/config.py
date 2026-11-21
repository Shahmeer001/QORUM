"""
Shared settings for all steps (01 -> 05).
Change numbers here only, so every script uses the same values.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
SNAPSHOT_DIR = BASE_DIR / "binance_snapshot"   # frozen Binance files (same numbers every run)
OUT_DIR = BASE_DIR / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Fixed file names
DATA_CSV = OUT_DIR / "btc_ohlcv.csv"
DATA_META = OUT_DIR / "data_meta.json"
TRADES_CSV = OUT_DIR / "dummy_trades_random.csv"
ENRICHED_CSV = OUT_DIR / "trades_with_roi_and_indicators.csv"
REPORT_PDF = OUT_DIR / "QUORUM_report.pdf"
STRATEGY_TRADES_CSV = OUT_DIR / "strategy_rsi_trades.csv"        # Method 2 (RSI rule) trades
STRATEGY_SUMMARY_CSV = OUT_DIR / "strategy_rsi_summary.csv"

# ---- Step 1: data (frozen window, Pakistan midnight 11 Nov 2025 -> 11 Nov 2026 = 1 year) ----
SYMBOL = "BTCUSDT"
INTERVAL = "5m"
INTERVAL_MINUTES = 5
START_UTC = "2025-11-10T19:00:00Z"        # 11 Nov 2025 00:00 PKT  (1 year)
END_UTC = "2026-11-10T19:00:00Z"          # 11 Nov 2026 00:00 PKT (excluded)
WARMUP_CANDLES = 300                      # extra candles before START for RSI / volume baseline

# ---- Step 2: random dummy trades ----
SEED = 42
N_TRADES = 40000         # each trade gets a DIFFERENT buy candle (no duplicates)
MIN_HOLD_MINUTES = 15
MAX_HOLD_MINUTES = 10 * 24 * 60   # 10 days

# ---- Step 5: Method 2, RSI-rule dummy trades ----
# Buy at the close of EVERY candle whose RSI is in RSI_BUY_ZONE (20-30).
# Sell at the close of the FIRST later candle whose RSI is in RSI_SELL_ZONE (70-80).
# Safety limit: if that never happens within STRATEGY_MAX_HOLD_MINUTES, sell then (exit = "time_limit").
STRATEGY_MAX_HOLD_MINUTES = MAX_HOLD_MINUTES

# ---- Step 3/4: analysis ----
HIGH_PROFIT_PCT = 10.0   # "high profit" = +10% ROI or more (supervisor's example was 20%)
LOSS_PCT = -10.0         # kept in CSV/JSON only (no charts)
RSI_PERIOD = 14
RSI_BUY_ZONE = (20, 30)
RSI_SELL_ZONE = (70, 80)

PATTERN_LENGTHS = (3, 7)              # previous 3 and 7 candles
PATTERN_INCLUDE_TRADE_CANDLE = False  # False = only the candles BEFORE the buy/sell candle
# Each candle's CLOSE vs the PREVIOUS candle's CLOSE: U = up, S = same, D = down.
# "Same" = change within +-0.025%. On this BTC 5m data that gives roughly
# U 35% / S 30% / D 35%, so all three states really occur (supervisor's 3 x 3 = 9).
SAME_TOL = 0.00025
MIN_PATTERN_COUNT = 30    # ignore patterns seen fewer times (too little evidence)
MIN_GROUP_WARN = 50


def load_meta() -> dict:
    if not DATA_META.exists():
        raise FileNotFoundError("data_meta.json missing. Run 01_download_data.py first.")
    return json.loads(DATA_META.read_text())


def load_ohlcv() -> pd.DataFrame:
    if not DATA_CSV.exists():
        raise FileNotFoundError("btc_ohlcv.csv missing. Run 01_download_data.py first.")
    df = pd.read_csv(DATA_CSV)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df
