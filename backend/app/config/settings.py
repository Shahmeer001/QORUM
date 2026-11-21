"""
QUORUM Central Settings
No magic numbers: all thresholds, caps, and parameters are defined here.
"""
from __future__ import annotations

import os
from pathlib import Path

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
