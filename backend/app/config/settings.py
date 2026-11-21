"""
QUORUM Central Settings
No magic numbers: all thresholds, caps, and parameters are defined here.
Handles time zone-aware decision cutoff for US Close across Daylight Saving Time.
"""
from __future__ import annotations

from datetime import datetime, time, timezone
import os
from pathlib import Path
from zoneinfo import ZoneInfo

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "quorum.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

KNOWLEDGE_DIR = BASE_DIR / "knowledge"
DATA_CACHE_DIR = BASE_DIR / "data_cache"

# Environment / Server
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
BRAIN = os.getenv("BRAIN", "rule").lower()  # "rule" or "fake"

# Debate & Turn settings
DEFAULT_MAX_TURNS = 3
TURN_CAP = 3
DEFAULT_CONFIDENCE = 65.0

# Trading & Risk Thresholds
ALLOW_SHORT = True
INITIAL_CAPITAL = 10000.0
DEFAULT_STOP_LOSS = 1.2        # %
DEFAULT_MAX_VOLATILITY = 2.5   # %
DEFAULT_MAX_DRAWDOWN = 5.0     # %

# Signal & Pattern Analysis (must match research/04_pattern_stats.py)
RSI_PERIOD = 14
RSI_BUY_ZONE = (20.0, 30.0)
RSI_SELL_ZONE = (70.0, 80.0)
SAME_TOLERANCE = 0.00025       # +-0.025% tolerance for 'S' candle
PATTERN_LENGTH = 3             # 3 candles (27 possible patterns: U-S-D combinations)

# Modes
VALID_MODES = ["single", "silent", "debate"]

# US Equity Close: Defined by timezone America/New_York at 4:00 PM (16:00),
# NOT a fixed UTC hour, so daylight saving time shifts are accurately handled.
US_TIMEZONE = ZoneInfo("America/New_York")
US_CLOSE_TIME = time(16, 0, 0)


def get_us_close_utc(day_str: str) -> datetime:
    """
    Computes the exact UTC timestamp of the US market close for a given calendar day.
    Automatically accounts for Eastern Daylight Time (EDT: UTC-4) vs Eastern Standard Time (EST: UTC-5).
    """
    dt = datetime.strptime(day_str, "%Y-%m-%d").date()
    local_close = datetime.combine(dt, US_CLOSE_TIME, tzinfo=US_TIMEZONE)
    return local_close.astimezone(timezone.utc)
