"""
STEP 4 — Candle patterns (supervisor's method) + pattern histogram + knowledge file for agents.

Pattern = how each candle CLOSED compared with the PREVIOUS candle's close:
    U = up, S = same (within +-0.05%), D = down      -> 3 options per candle
    2 candles = 3 x 3 = 9 patterns, 3 candles = 27, 7 candles = 3^7 = 2187.

For every pattern we count:
    total    = how many trades had this pattern
    high     = how many of those reached +HIGH_PROFIT_PCT (+10%, set in config.py)
    loss     = how many of those fell to LOSS_PCT (-10%) or worse
    rates    = high/total, loss/total, compared with the rate for ALL trades (lift)
    stable   = pattern beats the baseline in BOTH halves of the data (not just one lucky period)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import charts
from config import (ENRICHED_CSV, HIGH_PROFIT_PCT, LOSS_PCT, MIN_GROUP_WARN, MIN_PATTERN_COUNT,
                    OUT_DIR, PATTERN_INCLUDE_TRADE_CANDLE, PATTERN_LENGTHS, RSI_BUY_ZONE,
                    RSI_SELL_ZONE, SAME_TOL, load_meta, load_ohlcv)


def candle_moves(closes: np.ndarray, tol: float) -> np.ndarray:
    """U / S / D for each candle vs previous close. First candle has no previous -> ''."""
    change = np.r_[np.nan, closes[1:] / closes[:-1] - 1.0]
    moves = np.where(change > tol, "U", np.where(change < -tol, "D", "S"))
    moves[0] = ""
    return moves


def pattern_at(moves: np.ndarray, idx: np.ndarray, length: int, include_trade_candle: bool) -> list[str | None]:
    """Pattern of the previous `length` candles before the trade candle (oldest -> newest).
    If include_trade_candle=True, the window ends AT the trade candle instead."""
    out = []
    for i in idx:
        end = i if include_trade_candle else i - 1
        start = end - length + 1
        out.append("-".join(moves[start:end + 1]) if start >= 1 else None)
    return out


def pattern_table(trades: pd.DataFrame, col: str, base_high: float, base_loss: float,
                  split_time) -> pd.DataFrame:
    t = trades.dropna(subset=[col])
    g = t.groupby(col)
    stats = pd.DataFrame({
        "total": g.size(),
        "high": g["is_high_profit"].sum().astype(int),
        "loss": g["is_big_loss"].sum().astype(int),
        "win_rate_pct": g["is_profit"].mean() * 100,
        "avg_roi_pct": g["roi_pct"].mean(),
    })
    stats["high_rate_pct"] = stats["high"] / stats["total"] * 100
    stats["loss_rate_pct"] = stats["loss"] / stats["total"] * 100
    stats["high_lift"] = stats["high_rate_pct"] / base_high if base_high else np.nan
    stats["loss_lift"] = stats["loss_rate_pct"] / base_loss if base_loss else np.nan

    # Stability check: same pattern, first half of the data vs second half
    first = t["buy_time"] < split_time
    for name, part in (("h1", t[first]), ("h2", t[~first])):
        pg = part.groupby(col)
        stats[f"high_rate_{name}"] = pg["is_high_profit"].mean() * 100
        stats[f"loss_rate_{name}"] = pg["is_big_loss"].mean() * 100
    stats["stable_good"] = (stats["high_rate_h1"] > base_high) & (stats["high_rate_h2"] > base_high)
    stats["stable_bad"] = (stats["loss_rate_h1"] > base_loss) & (stats["loss_rate_h2"] > base_loss)
    stats["enough_data"] = stats["total"] >= MIN_PATTERN_COUNT
    return stats.sort_values("total", ascending=False)


def top(stats: pd.DataFrame, by: str, n: int = 10) -> pd.DataFrame:
    s = stats[stats["enough_data"]]
    return s.sort_values([by, "total"], ascending=[False, False]).head(n)


def as_records(df: pd.DataFrame, n: int = 5) -> list[dict]:
    keep = ["total", "high_rate_pct", "loss_rate_pct", "avg_roi_pct", "high_lift", "loss_lift",
            "stable_good", "stable_bad"]
    recs = []
    for pat, row in df.head(n).iterrows():
        r = {"pattern": pat}
        for k in keep:
            v = row[k]
            r[k] = bool(v) if isinstance(v, (bool, np.bool_)) else (int(v) if k == "total" else round(float(v), 3))
        recs.append(r)
    return recs


def main() -> None:
    print("STEP 4: Candle patterns + histogram + agent knowledge file...")
    ohlcv = load_ohlcv()
    trades = pd.read_csv(ENRICHED_CSV)
    trades["buy_time"] = pd.to_datetime(trades["buy_time"], utc=True)

    moves = candle_moves(ohlcv["Close"].to_numpy(dtype=float), SAME_TOL)
    inc = PATTERN_INCLUDE_TRADE_CANDLE
    for L in PATTERN_LENGTHS:
        trades[f"buy_pattern_{L}"] = pattern_at(moves, trades["buy_idx"].to_numpy(), L, inc)
        trades[f"sell_pattern_{L}"] = pattern_at(moves, trades["sell_idx"].to_numpy(), L, inc)
    trades.to_csv(OUT_DIR / "trades_with_patterns.csv", index=False)

    # Successful (+10%) trades only, with their previous 3 / 7 candles
    profit_cols = (["trade_id", "buy_time", "sell_time", "buy_price", "sell_price", "roi_pct"]
                   + [f"{s}_{c}" for s in ("buy", "sell")
                      for c in ("rsi", "volume", "liquidity", "relvolume", "relliquidity")]
                   + [f"{s}_pattern_{L}" for L in PATTERN_LENGTHS for s in ("buy", "sell")])
    trades.loc[trades["is_high_profit"], profit_cols].to_csv(
        OUT_DIR / "high_profit_trades_with_patterns.csv", index=False)

    base_high = float(trades["is_high_profit"].mean() * 100)
    base_loss = float(trades["is_big_loss"].mean() * 100)
    split_time = trades["buy_time"].median()
    print(f"  Baseline: +{HIGH_PROFIT_PCT:g}% rate = {base_high:.2f}% | {LOSS_PCT:g}% rate = {base_loss:.2f}%")
    if trades["is_high_profit"].sum() < MIN_GROUP_WARN:
        print(f"  WARNING: only {int(trades['is_high_profit'].sum())} trades reached "
              f"+{HIGH_PROFIT_PCT:g}%. Pattern results for 'good' patterns are weak.")

    for old in OUT_DIR.glob("chart4_*.png"):
        old.unlink(missing_ok=True)

    # ---- Frequency count of EVERY pattern: how often it appeared, how often it gave profit ----
    for side in ("buy", "sell"):
        for L in PATTERN_LENGTHS:
            t = trades.dropna(subset=[f"{side}_pattern_{L}"])
            g = t.groupby(f"{side}_pattern_{L}")
            freq = pd.DataFrame({
                "times_appeared": g.size(),
                "times_profit": g["is_profit"].sum().astype(int),
                f"times_plus{HIGH_PROFIT_PCT:g}": g["is_high_profit"].sum().astype(int),
                "avg_roi_pct": g["roi_pct"].mean().round(3),
            })
            freq.insert(2, "profit_rate_pct", (freq["times_profit"] / freq["times_appeared"] * 100).round(2))
            freq[f"plus{HIGH_PROFIT_PCT:g}_rate_pct"] = (
                freq[f"times_plus{HIGH_PROFIT_PCT:g}"] / freq["times_appeared"] * 100).round(2)
            hp_c, hp_r = f"times_plus{HIGH_PROFIT_PCT:g}", f"plus{HIGH_PROFIT_PCT:g}_rate_pct"
            freq = freq[["times_appeared", "times_profit", "profit_rate_pct", hp_c, hp_r, "avg_roi_pct"]]
            freq = freq.sort_values(["times_appeared", "times_profit"], ascending=False)
            freq.to_csv(OUT_DIR / f"pattern_frequency_{side}_{L}candle.csv", index_label="pattern")

    n_high = int(trades["is_high_profit"].sum())
    hp = f"+{HIGH_PROFIT_PCT:g}%"
    knowledge = {}
    chart_no = 1
    for side in ("buy", "sell"):
        for L in PATTERN_LENGTHS:
            col = f"{side}_pattern_{L}"
            stats = pattern_table(trades, col, base_high, base_loss, split_time)
            stats.to_csv(OUT_DIR / f"pattern_stats_{side}_{L}candle.csv", index_label="pattern")
            good = top(stats, "high_rate_pct")
            bad = top(stats, "loss_rate_pct")

            # Which previous-candle pattern REPEATED most among the successful trades?
            repeated = stats[stats["high"] > 0].sort_values(["high", "high_rate_pct"], ascending=False).head(10).copy()
            repeated["share_of_profit_trades_pct"] = repeated["high"] / max(n_high, 1) * 100
            # Typical volume / liquidity (at this side: buy or sell) of the +10% trades with each pattern
            hi = trades[trades["is_high_profit"]].groupby(col)[[f"{side}_relvolume", f"{side}_relliquidity"]].median()
            repeated["median_rel_volume"] = hi[f"{side}_relvolume"].reindex(repeated.index)
            repeated["median_rel_liquidity"] = hi[f"{side}_relliquidity"].reindex(repeated.index)
            repeated["volume_level"] = repeated["median_rel_volume"].map(charts.level)
            repeated["liquidity_level"] = repeated["median_rel_liquidity"].map(charts.level)
            repeated[["high", "share_of_profit_trades_pct", "total", "high_rate_pct", "high_lift",
                      "stable_good", "enough_data", "volume_level", "liquidity_level",
                      "median_rel_volume", "median_rel_liquidity"]].to_csv(
                OUT_DIR / f"most_repeated_{side}_patterns_{L}candle_plus{HIGH_PROFIT_PCT:g}.csv",
                index_label="pattern")

            knowledge[f"{side}_{L}candle"] = {
                "patterns_seen": int(len(stats)),
                "patterns_with_enough_data": int(stats["enough_data"].sum()),
                "most_repeated_before_high_profit": [
                    {"pattern": p, "times_in_high_profit_trades": int(r["high"]),
                     "share_of_high_profit_trades_pct": round(float(r["share_of_profit_trades_pct"]), 3),
                     "times_seen_in_all_trades": int(r["total"]),
                     "high_rate_pct": round(float(r["high_rate_pct"]), 3),
                     "stable_good": bool(r["stable_good"])}
                    for p, r in repeated.head(5).iterrows()],
                "best_for_high_profit": as_records(good),
                "avoid_high_loss": as_records(bad),
            }
            if side == "buy" or L == min(PATTERN_LENGTHS):
                # Profit-only charts: hit-rate per pattern
                charts.pattern_bars(good, "high_rate_pct", base_high,
                                    f"{side.upper()} patterns (previous {L} candles): % reaching {hp}",
                                    "% of trades with this pattern",
                                    OUT_DIR / f"chart4_{chart_no}_profit_rate_{side}_{L}.png",
                                    charts.GREEN)
                chart_no += 1
            # Most repeated previous-candle patterns among successful trades (BUY side and SELL side)
            when = "before the BUY of" if side == "buy" else "before the SELL of"
            charts.repeat_bars(repeated, n_high,
                               f"Most repeated previous {L}-candle patterns {when} {hp} trades",
                               OUT_DIR / f"chart4_{chart_no}_most_repeated_{side}_{L}.png",
                               vol_levels=list(repeated["volume_level"]),
                               liq_levels=list(repeated["liquidity_level"]))
            chart_no += 1
            print(f"  {col}: {len(stats)} patterns, {int(stats['enough_data'].sum())} with >= "
                  f"{MIN_PATTERN_COUNT} trades | most repeated before {hp}: "
                  f"{repeated.index[0] if len(repeated) else '-'}")

    # RSI rule numbers from step 3, so agents get everything in one file
    summary = pd.read_csv(OUT_DIR / "summary_stats.csv", index_col=0)["value"]

    def num(key: str):
        try:
            return round(float(summary[key]), 3)
        except (KeyError, ValueError):
            return None

    agent_file = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data": load_meta(),
        "how_to_read": {
            "pattern": "U/S/D per candle vs previous close (S = within +-%.2f%%), oldest -> newest, "
                       "%s" % (SAME_TOL * 100, "last letter = the buy/sell candle itself" if PATTERN_INCLUDE_TRADE_CANDLE
                               else "candles BEFORE the buy/sell candle (last letter = candle just before it)"),
            "most_repeated": f"patterns seen most often among the {hp} trades (raw count + share)",
            "high_rate_pct": f"% of trades with this pattern that reached +{HIGH_PROFIT_PCT:g}%",
            "loss_rate_pct": f"% of trades with this pattern that fell to {LOSS_PCT:g}% or worse",
            "lift": "pattern rate / rate for all trades (1.0 = no better than random)",
            "stable": "beat the baseline in both halves of the data",
            "min_trades_per_pattern": MIN_PATTERN_COUNT,
        },
        "baseline": {
            "total_trades": int(len(trades)),
            "win_rate_pct": round(float(trades["is_profit"].mean() * 100), 3),
            "high_profit_rate_pct": round(base_high, 3),
            "big_loss_rate_pct": round(base_loss, 3),
        },
        "rsi_rule": {
            "buy_zone": list(RSI_BUY_ZONE),
            "sell_zone": list(RSI_SELL_ZONE),
            "trades_bought_in_zone": num("rule_buy_zone_trades"),
            "win_rate_pct_when_bought_in_zone": num("rule_buy_zone_win_rate_pct"),
            "avg_roi_pct_when_bought_in_zone": num("rule_buy_zone_avg_roi_pct"),
        },
        "patterns": knowledge,
        "caveats": [
            "Random dummy trades on historical data, no fees or slippage.",
            "Look-back statistics, not a guarantee for the future.",
        ],
    }
    out = OUT_DIR / "agent_pattern_knowledge.json"
    out.write_text(json.dumps(agent_file, indent=2))
    print(f"Saved: pattern_stats_*.csv, chart4_*.png, {out.name}")
    print("STEP 4 DONE")


if __name__ == "__main__":
    main()
