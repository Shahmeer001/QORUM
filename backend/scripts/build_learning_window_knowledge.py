"""
Builds empirical pattern knowledge strictly from the learning window (2022-01-03 to 2024-12-31).
The test window (2025-01-01 to 2026-11-20) is held out as Out-of-Sample evaluation data.
DO NOT use research/output data.
"""
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import numpy as np
import pandas as pd

LEARNING_START = "2022-01-03"
LEARNING_END = "2024-12-31"
TEST_START = "2025-01-01"
TEST_END = "2026-11-20"
SAME_TOLERANCE = 0.00025

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data_cache"
KNOWLEDGE_DIR = ROOT / "knowledge"
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)


def compute_pattern_stats(closes: np.ndarray, dates: list, market_name: str) -> dict:
    if len(closes) < 10:
        return {}

    returns = closes[1:] / closes[:-1] - 1.0
    moves = np.where(returns > SAME_TOLERANCE, "U", np.where(returns < -SAME_TOLERANCE, "D", "S"))

    # Baseline win rate on forward 1-period return
    fwd_returns = returns[3:]
    baseline_win_rate = float(np.mean(fwd_returns > 0.0) * 100.0)

    pattern_counts = defaultdict(int)
    pattern_wins = defaultdict(int)

    for i in range(len(moves) - 3):
        pat = f"{moves[i]}-{moves[i+1]}-{moves[i+2]}"
        fwd = returns[i + 3]
        pattern_counts[pat] += 1
        if fwd > 0.0:
            pattern_wins[pat] += 1

    pattern_dict = {}
    for pat, count in pattern_counts.items():
        win_rate = (pattern_wins[pat] / count * 100.0) if count > 0 else 50.0
        lift = round(win_rate / baseline_win_rate, 4) if baseline_win_rate > 0 else 1.0
        pattern_dict[pat] = {
            "count": count,
            "win_rate_pct": round(win_rate, 2),
            "lift": lift,
        }

    return {
        "market": market_name,
        "split": {
            "learning_window": [LEARNING_START, LEARNING_END],
            "test_window_held_out": [TEST_START, TEST_END],
            "note": "Rebuilt strictly from learning window. Out-of-sample test window held out untouched.",
        },
        "baseline": {
            "total_bars": len(closes),
            "win_rate_pct": round(baseline_win_rate, 2),
        },
        "patterns": pattern_dict,
    }


def main():
    print("Building knowledge strictly for learning window (2022-01-03 to 2024-12-31)...")

    # 1. SPY Daily Knowledge
    spy_path = DATA_DIR / "spy_daily.csv"
    df_spy = pd.read_csv(spy_path)
    df_spy["dt"] = pd.to_datetime(df_spy["Date"].astype(str).str.split().str[0], format="%d/%m/%Y").dt.date
    learn_spy = df_spy[(df_spy["dt"] >= pd.to_datetime(LEARNING_START).date()) & (df_spy["dt"] <= pd.to_datetime(LEARNING_END).date())].sort_values("dt").reset_index(drop=True)
    print(f"SPY learning bars: {len(learn_spy)} (from {learn_spy['dt'].iloc[0]} to {learn_spy['dt'].iloc[-1]})")

    spy_stats = compute_pattern_stats(learn_spy["Close"].values, learn_spy["dt"].tolist(), "US")
    us_file = KNOWLEDGE_DIR / "us.json"
    with open(us_file, "w", encoding="utf-8") as f:
        json.dump(spy_stats, f, indent=2)
    print(f"Saved US knowledge to {us_file}")

    # 2. BTC Hourly Knowledge (daily close aggregated from 1h data aligned to US close)
    btc_path = DATA_DIR / "btc_1h.csv"
    df_btc = pd.read_csv(btc_path)
    df_btc["open_dt"] = pd.to_datetime(df_btc["timestamp"])
    learn_btc = df_btc[(df_btc["open_dt"] >= pd.to_datetime(f"{LEARNING_START} 00:00:00+00:00")) & (df_btc["open_dt"] <= pd.to_datetime(f"{LEARNING_END} 23:59:59+00:00"))].sort_values("open_dt").reset_index(drop=True)
    print(f"BTC learning 1h bars: {len(learn_btc)} (from {learn_btc['open_dt'].iloc[0]} to {learn_btc['open_dt'].iloc[-1]})")

    btc_stats = compute_pattern_stats(learn_btc["Close"].values, learn_btc["open_dt"].tolist(), "CRYPTO")
    crypto_file = KNOWLEDGE_DIR / "crypto.json"
    with open(crypto_file, "w", encoding="utf-8") as f:
        json.dump(btc_stats, f, indent=2)
    print(f"Saved CRYPTO knowledge to {crypto_file}")


if __name__ == "__main__":
    main()
