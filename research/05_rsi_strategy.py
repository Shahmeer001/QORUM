"""
STEP 5 — Method 2: dummy trades made by the RSI rule (supervisor: "RSI 20-30 buy, 70-80 sell").

    Buy  = close of every candle whose RSI(14) is 20-30
    Sell = close of the first later candle whose RSI(14) is 70-80
           (safety: sell after STRATEGY_MAX_HOLD_MINUTES if RSI never gets there)

Then, exactly like Method 1:
    ROI = (Sell / Buy) x 100 - 100
    Profitable trades (ROI > 0): volume and liquidity at buy and sell, compared with all RSI-rule trades
    Previous 3 and 7 candles before each profitable buy: which pattern repeats most
    Comparison with Method 1 (random trades)
"""
from __future__ import annotations

import importlib

import numpy as np
import pandas as pd

import charts
from config import (MIN_PATTERN_COUNT, OUT_DIR, PATTERN_INCLUDE_TRADE_CANDLE, PATTERN_LENGTHS,
                    RSI_BUY_ZONE, RSI_PERIOD, RSI_SELL_ZONE, SAME_TOL, STRATEGY_MAX_HOLD_MINUTES,
                    STRATEGY_SUMMARY_CSV, STRATEGY_TRADES_CSV, load_meta, load_ohlcv)

step3 = importlib.import_module("03_roi_and_indicators")   # same RSI as Method 1
step4 = importlib.import_module("04_pattern_stats")        # same U/S/D patterns as Method 1


def make_trades(ohlcv: pd.DataFrame, step: int) -> tuple[pd.DataFrame, int]:
    rsi = ohlcv["RSI"].to_numpy()
    n = len(ohlcv)
    first = int(ohlcv["is_warmup"].sum())
    max_hold = STRATEGY_MAX_HOLD_MINUTES // step

    buy_idx = np.where((rsi >= RSI_BUY_ZONE[0]) & (rsi <= RSI_BUY_ZONE[1]))[0]
    buy_idx = buy_idx[(buy_idx >= first) & (buy_idx < n - 1)]
    sell_zone = np.where((rsi >= RSI_SELL_ZONE[0]) & (rsi <= RSI_SELL_ZONE[1]))[0]

    # first sell-zone candle AFTER each buy candle
    pos = np.searchsorted(sell_zone, buy_idx + 1)
    has_signal = pos < len(sell_zone)
    signal_idx = np.where(has_signal, sell_zone[np.minimum(pos, len(sell_zone) - 1)], n + max_hold)

    limit_idx = buy_idx + max_hold
    sell_idx = np.minimum(signal_idx, limit_idx)
    exit_reason = np.where(signal_idx <= limit_idx, "rsi_70_80", "time_limit")

    still_open = sell_idx >= n          # no sell before the data ends -> trade not finished, dropped
    buy_idx, sell_idx, exit_reason = buy_idx[~still_open], sell_idx[~still_open], exit_reason[~still_open]

    ts, close = ohlcv["timestamp"].to_numpy(), ohlcv["Close"].to_numpy()
    trades = pd.DataFrame({
        "trade_id": np.arange(1, len(buy_idx) + 1),
        "buy_idx": buy_idx, "sell_idx": sell_idx,
        "buy_time": ts[buy_idx], "sell_time": ts[sell_idx],
        "buy_price": close[buy_idx], "sell_price": close[sell_idx],
        "hold_candles": sell_idx - buy_idx,
        "hold_hours": (sell_idx - buy_idx) * step / 60.0,
        "exit_reason": exit_reason,
    })
    return trades, int(still_open.sum())


def pattern_table(trades: pd.DataFrame, col: str, base_win: float, split_time) -> pd.DataFrame:
    """Per pattern: how often it appeared, how many of those trades were profitable."""
    t = trades.dropna(subset=[col])
    g = t.groupby(col)
    stats = pd.DataFrame({
        "total": g.size(),
        "high": g["is_profit"].sum().astype(int),          # 'high' = profitable (same column name as Method 1 charts)
        "avg_roi_pct": g["roi_pct"].mean(),
    })
    stats["high_rate_pct"] = stats["high"] / stats["total"] * 100       # win rate of this pattern
    stats["lift"] = stats["high_rate_pct"] / base_win if base_win else np.nan
    first = t["buy_time"] < split_time
    stats["win_rate_h1"] = t[first].groupby(col)["is_profit"].mean() * 100
    stats["win_rate_h2"] = t[~first].groupby(col)["is_profit"].mean() * 100
    stats["stable_good"] = (stats["win_rate_h1"] > base_win) & (stats["win_rate_h2"] > base_win)
    stats["enough_data"] = stats["total"] >= MIN_PATTERN_COUNT
    # Many RSI-rule trades bought in the same dip are sold at the SAME candle.
    # unique_moments = how many different buy/sell candles are behind the trade count.
    idx_col = "sell_idx" if col.startswith("sell_") else "buy_idx"
    stats["unique_moments"] = g[idx_col].nunique()
    stats["unique_profitable_moments"] = t[t["is_profit"]].groupby(col)[idx_col].nunique()
    stats["unique_profitable_moments"] = stats["unique_profitable_moments"].fillna(0).astype(int)
    return stats


def main() -> None:
    print("STEP 5: Method 2 - RSI rule dummy trades (buy RSI 20-30, sell RSI 70-80)...")
    ohlcv = load_ohlcv()
    step = load_meta()["interval_minutes"]

    # Same indicators as Method 1
    ohlcv["RSI"] = step3.calc_rsi(ohlcv["Close"], RSI_PERIOD)
    ohlcv["Liquidity"] = ohlcv["QuoteVolume"] if "QuoteVolume" in ohlcv.columns else \
        ohlcv["Volume"] * (ohlcv["High"] + ohlcv["Low"] + ohlcv["Close"]) / 3.0
    day = max(1, 1440 // step)
    ohlcv["RelVolume"] = ohlcv["Volume"] / ohlcv["Volume"].rolling(day, min_periods=day // 2).median()
    ohlcv["RelLiquidity"] = ohlcv["Liquidity"] / ohlcv["Liquidity"].rolling(day, min_periods=day // 2).median()

    for old in OUT_DIR.glob("chart6_*.png"):     # remove charts of earlier runs
        old.unlink(missing_ok=True)

    trades, dropped_open = make_trades(ohlcv, step)
    trades["buy_time"] = pd.to_datetime(trades["buy_time"], utc=True)
    trades["sell_time"] = pd.to_datetime(trades["sell_time"], utc=True)

    cols = ["RSI", "Volume", "Liquidity", "RelVolume", "RelLiquidity"]
    for side in ("buy", "sell"):
        vals = ohlcv.loc[trades[f"{side}_idx"].to_numpy(), cols].reset_index(drop=True)
        vals.columns = [f"{side}_{c.lower()}" for c in cols]
        trades = pd.concat([trades, vals], axis=1)

    trades["roi_pct"] = trades["sell_price"] / trades["buy_price"] * 100.0 - 100.0
    trades["is_profit"] = trades["roi_pct"] > 0

    moves = step4.candle_moves(ohlcv["Close"].to_numpy(dtype=float), SAME_TOL)
    for L in PATTERN_LENGTHS:
        trades[f"buy_pattern_{L}"] = step4.pattern_at(moves, trades["buy_idx"].to_numpy(), L,
                                                      PATTERN_INCLUDE_TRADE_CANDLE)
        trades[f"sell_pattern_{L}"] = step4.pattern_at(moves, trades["sell_idx"].to_numpy(), L,
                                                       PATTERN_INCLUDE_TRADE_CANDLE)
    trades.to_csv(STRATEGY_TRADES_CSV, index=False)
    profit = trades[trades["is_profit"]]
    profit.to_csv(OUT_DIR / "strategy_rsi_profitable_trades.csv", index=False)

    # ---- Method 1 numbers for comparison ----
    m1 = pd.read_csv(OUT_DIR / "trades_with_roi_and_indicators.csv")
    base_win = float(trades["is_profit"].mean() * 100)
    entries = int((np.diff(np.r_[-10, trades["buy_idx"].to_numpy()]) > 1).sum())

    summary = {
        "trades": len(trades),
        "separate_rsi_20_30_entries": entries,
        "dropped_still_open_at_end": dropped_open,
        "exit_rsi_70_80": int((trades["exit_reason"] == "rsi_70_80").sum()),
        "exit_time_limit": int((trades["exit_reason"] == "time_limit").sum()),
        "win_rate_pct": base_win,
        "avg_roi_pct": float(trades["roi_pct"].mean()),
        "median_roi_pct": float(trades["roi_pct"].median()),
        "avg_profit_of_winners_pct": float(profit["roi_pct"].mean()),
        "avg_loss_of_losers_pct": float(trades.loc[~trades["is_profit"], "roi_pct"].mean()),
        "best_trade_pct": float(trades["roi_pct"].max()),
        "worst_trade_pct": float(trades["roi_pct"].min()),
        "trades_plus10": int((trades["roi_pct"] >= 10).sum()),
        "median_hold_hours": float(trades["hold_hours"].median()),
        "profitable_trades": len(profit),
        "unique_sell_candles": int(trades["sell_idx"].nunique()),
        "median_rel_volume_buy_ALL": float(trades["buy_relvolume"].median()),
        "median_rel_volume_buy_PROFIT": float(profit["buy_relvolume"].median()),
        "median_rel_volume_sell_ALL": float(trades["sell_relvolume"].median()),
        "median_rel_volume_sell_PROFIT": float(profit["sell_relvolume"].median()),
        "median_rel_liquidity_buy_ALL": float(trades["buy_relliquidity"].median()),
        "median_rel_liquidity_buy_PROFIT": float(profit["buy_relliquidity"].median()),
        "median_rel_liquidity_sell_ALL": float(trades["sell_relliquidity"].median()),
        "median_rel_liquidity_sell_PROFIT": float(profit["sell_relliquidity"].median()),
        "avg_rsi_buy": float(trades["buy_rsi"].mean()),
        "avg_rsi_sell": float(trades["sell_rsi"].mean()),
        # Method 1 (random) for comparison
        "m1_trades": len(m1),
        "m1_win_rate_pct": float(m1["is_profit"].mean() * 100),
        "m1_avg_roi_pct": float(m1["roi_pct"].mean()),
        "m1_median_roi_pct": float(m1["roi_pct"].median()),
        "m1_avg_profit_of_winners_pct": float(m1.loc[m1["is_profit"], "roi_pct"].mean()),
        "m1_avg_loss_of_losers_pct": float(m1.loc[~m1["is_profit"], "roi_pct"].mean()),
        "m1_median_hold_hours": float(m1["hold_hours"].median()),
    }

    # ---- patterns before profitable RSI-rule buys ----
    split_time = trades["buy_time"].median()
    for side in ("buy", "sell"):
        for L in PATTERN_LENGTHS:
            stats = pattern_table(trades, f"{side}_pattern_{L}", base_win, split_time)
            stats.sort_values("total", ascending=False).to_csv(
                OUT_DIR / f"strategy_pattern_stats_{side}_{L}candle.csv", index_label="pattern")
            # Frequency count of EVERY pattern: how often it appeared, how often it gave profit
            freq = pd.DataFrame({
                "times_appeared": stats["total"],
                "times_profit": stats["high"],
                "profit_rate_pct": stats["high_rate_pct"].round(2),
                "avg_roi_pct": stats["avg_roi_pct"].round(3),
                f"distinct_{side}_candles": stats["unique_moments"],
            }).sort_values(["times_appeared", "times_profit"], ascending=False)
            freq.to_csv(OUT_DIR / f"strategy_pattern_frequency_{side}_{L}candle.csv", index_label="pattern")
            rep = stats[stats["high"] > 0].sort_values(["high", "high_rate_pct"], ascending=False).head(10).copy()
            rep["share_of_profit_trades_pct"] = rep["high"] / max(len(profit), 1) * 100
            rep[["high", "share_of_profit_trades_pct", "total", "high_rate_pct", "lift", "stable_good",
                 "enough_data", "unique_profitable_moments", "unique_moments"]].rename(columns={"high": "times_in_profitable", "high_rate_pct": "win_rate_pct"}).to_csv(
                OUT_DIR / f"strategy_most_repeated_{side}_patterns_{L}candle.csv", index_label="pattern")
            # BUY side: chart6_3 (3 candles), chart6_4 (7 candles); SELL side: chart6_5, chart6_6
            num_ = (3 if side == "buy" else 5) + (0 if L == min(PATTERN_LENGTHS) else 1)
            when = "before the BUY of" if side == "buy" else "before the SELL of"
            charts.repeat_bars(rep, len(profit),
                               f"RSI rule: most repeated previous {L}-candle patterns {when} profitable trades",
                               OUT_DIR / f"chart6_{num_}_most_repeated_{side}_{L}.png")
            summary[f"top_{side}_pattern_{L}"] = rep.index[0] if len(rep) else ""
            summary[f"top_{side}_pattern_{L}_times"] = int(rep["high"].iloc[0]) if len(rep) else 0
            summary[f"top_{side}_pattern_{L}_win_rate_pct"] = float(rep["high_rate_pct"].iloc[0]) if len(rep) else float("nan")
            summary[f"stable_{side}_patterns_{L}"] = int(stats[stats["enough_data"]]["stable_good"].sum())

    pd.Series(summary).to_csv(STRATEGY_SUMMARY_CSV, header=["value"])
    for k, v in summary.items():
        print(f"  {k:38s} {v:.2f}" if isinstance(v, float) else f"  {k:38s} {v}")

    # ---- charts ----
    # Volume / liquidity are reported as numbers only (supervisor asked histograms for the patterns).
    charts.grouped_bars(
        ["Win rate %", "Avg ROI %", "Avg profit of winners %", "Avg loss of losers %"],
        [([summary["m1_win_rate_pct"], summary["m1_avg_roi_pct"], summary["m1_avg_profit_of_winners_pct"],
           summary["m1_avg_loss_of_losers_pct"]], "Method 1: random trades", charts.GREY),
         ([summary["win_rate_pct"], summary["avg_roi_pct"], summary["avg_profit_of_winners_pct"],
           summary["avg_loss_of_losers_pct"]], "Method 2: RSI rule trades", charts.BLUE)],
        "Random trades vs RSI rule trades (buy RSI 20-30, sell RSI 70-80)", "Value",
        OUT_DIR / "chart6_1_random_vs_rsi_rule.png")
    charts.profit_histogram(profit["roi_pct"], "RSI rule: ROI of profitable trades", "ROI %",
                            OUT_DIR / "chart6_2_roi_profitable.png", charts.BLUE,
                            all_mean=summary["avg_roi_pct"])

    print(f"Saved: {STRATEGY_TRADES_CSV.name}, strategy_rsi_profitable_trades.csv, "
          f"strategy_*patterns*.csv, {STRATEGY_SUMMARY_CSV.name}, chart6_*.png")
    print("STEP 5 DONE")


if __name__ == "__main__":
    main()
