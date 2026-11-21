"""
STEP 2 — Random dummy trades (supervisor: "random buying", thousands of fake trades).
Each trade: buy at the CLOSE of a random candle, hold a random time, sell at a later CLOSE.
Every trade uses a different buy candle, so no trade is counted twice.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from config import (MAX_HOLD_MINUTES, MIN_HOLD_MINUTES, N_TRADES, SEED, TRADES_CSV,
                    load_meta, load_ohlcv)


def main() -> None:
    print("STEP 2: Random dummy trades...")
    df = load_ohlcv()
    meta = load_meta()
    step = meta["interval_minutes"]

    # FIX: hold time is set in minutes, then converted to candles,
    # so 10 days stays 10 days even if the candle size changes (5m vs 1h).
    min_hold = max(1, math.ceil(MIN_HOLD_MINUTES / step))
    max_hold = max(min_hold, MAX_HOLD_MINUTES // step)

    n = len(df)
    last_buy = n - 1 - min_hold
    if last_buy < 1:
        raise RuntimeError("Not enough candles")

    # Buys only inside the study window (warm-up candles are only for RSI / volume baseline)
    first_buy = int(df["is_warmup"].sum()) if "is_warmup" in df.columns else 0
    rng = np.random.default_rng(SEED)
    n_trades = min(N_TRADES, last_buy - first_buy + 1)
    # replace=False -> every trade has a different buy candle (no duplicates)
    buy_idx = np.sort(first_buy + rng.choice(last_buy - first_buy + 1, size=n_trades, replace=False))

    longest_allowed = np.minimum(max_hold, n - 1 - buy_idx)
    hold = min_hold + np.floor(rng.random(n_trades) * (longest_allowed - min_hold + 1)).astype(int)
    sell_idx = buy_idx + hold

    trades = pd.DataFrame({
        "trade_id": np.arange(1, n_trades + 1),
        "buy_idx": buy_idx,
        "sell_idx": sell_idx,
        "buy_time": df["timestamp"].to_numpy()[buy_idx],
        "sell_time": df["timestamp"].to_numpy()[sell_idx],
        "buy_price": df["Close"].to_numpy()[buy_idx],
        "sell_price": df["Close"].to_numpy()[sell_idx],
        "hold_candles": hold,
        "hold_hours": hold * step / 60.0,
    })
    trades.to_csv(TRADES_CSV, index=False)

    print(f"Candles: {n} ({step}-minute) | hold: {min_hold}-{max_hold} candles")
    print(f"Saved {len(trades)} dummy trades (seed={SEED}) -> {TRADES_CSV}")
    print(trades.head(3).to_string(index=False))
    print("STEP 2 DONE")


if __name__ == "__main__":
    main()
