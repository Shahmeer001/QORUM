"""
STEP 3 — ROI of every dummy trade + RSI / Volume / Liquidity at buy and sell time.
Look-back: how do high-profit (+HIGH_PROFIT_PCT) and loss (LOSS_PCT) trades differ from ALL trades?
(Comparing with ALL trades = the baseline. Without it a % means nothing.)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import charts
from config import (ENRICHED_CSV, HIGH_PROFIT_PCT, LOSS_PCT, MIN_GROUP_WARN, OUT_DIR,
                    RSI_BUY_ZONE, RSI_PERIOD, RSI_SELL_ZONE, TRADES_CSV, load_meta,
                    load_ohlcv)


def calc_rsi(closes: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's RSI."""
    delta = closes.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rsi = 100 - 100 / (1 + avg_gain / avg_loss)
    return rsi.where(avg_loss != 0, 100.0)  # no losses at all -> RSI = 100


def in_zone(s: pd.Series, zone: tuple[float, float]) -> pd.Series:
    return s.between(zone[0], zone[1])


def main() -> None:
    print("STEP 3: ROI + RSI / Volume / Liquidity look-back...")
    ohlcv = load_ohlcv()
    step = load_meta()["interval_minutes"]
    trades = pd.read_csv(TRADES_CSV)
    trades["buy_time"] = pd.to_datetime(trades["buy_time"], utc=True)

    # FIX: make sure step 2 was run on THIS data file (indexes would be wrong otherwise)
    if trades["buy_idx"].max() >= len(ohlcv) or not (
        ohlcv["timestamp"].to_numpy()[trades["buy_idx"]] == trades["buy_time"].to_numpy()
    ).all():
        raise RuntimeError("Data changed after step 2. Run 02_random_dummy_trades.py again.")

    # ---- indicators on every candle ----
    ohlcv["RSI"] = calc_rsi(ohlcv["Close"], RSI_PERIOD)
    if "QuoteVolume" in ohlcv.columns:
        ohlcv["Liquidity"] = ohlcv["QuoteVolume"]          # USDT actually traded (from Binance)
    else:
        typical = (ohlcv["High"] + ohlcv["Low"] + ohlcv["Close"]) / 3.0
        ohlcv["Liquidity"] = ohlcv["Volume"] * typical      # approx. USD traded
    # Relative values: volume compared with the median of the last 24 hours.
    # Raw BTC volume changes a lot month to month, so 1.0 = "normal", 2.0 = "double normal".
    day = max(1, 1440 // step)
    ohlcv["RelVolume"] = ohlcv["Volume"] / ohlcv["Volume"].rolling(day, min_periods=day // 2).median()
    ohlcv["RelLiquidity"] = ohlcv["Liquidity"] / ohlcv["Liquidity"].rolling(day, min_periods=day // 2).median()

    cols = ["RSI", "Volume", "Liquidity", "RelVolume", "RelLiquidity"]
    for side in ("buy", "sell"):
        vals = ohlcv.loc[trades[f"{side}_idx"].to_numpy(), cols].reset_index(drop=True)
        vals.columns = [f"{side}_{c.lower()}" for c in cols]
        trades = pd.concat([trades, vals], axis=1)

    # ---- ROI and groups ----
    trades["roi_pct"] = trades["sell_price"] / trades["buy_price"] * 100.0 - 100.0
    trades["is_profit"] = trades["roi_pct"] > 0
    trades["is_high_profit"] = trades["roi_pct"] >= HIGH_PROFIT_PCT
    trades["is_big_loss"] = trades["roi_pct"] <= LOSS_PCT
    trades.to_csv(ENRICHED_CSV, index=False)

    allt = trades
    high = trades[trades["is_high_profit"]]
    loss = trades[trades["is_big_loss"]]
    if len(high) < MIN_GROUP_WARN:
        print(f"WARNING: only {len(high)} trades reached +{HIGH_PROFIT_PCT:g}%. Results are weak. "
              f"Consider lowering HIGH_PROFIT_PCT in config.py.")

    def pct(g: pd.DataFrame, col: str, zone) -> float:
        return float(in_zone(g[col], zone).mean() * 100) if len(g) else float("nan")

    # ---- direct test of the supervisor's RSI rule on the random trades ----
    rule_buy = trades[in_zone(trades["buy_rsi"], RSI_BUY_ZONE)]
    rule_both = rule_buy[in_zone(rule_buy["sell_rsi"], RSI_SELL_ZONE)]

    def rate(g: pd.DataFrame, col: str) -> float:
        return float(g[col].mean() * 100) if len(g) else float("nan")

    summary = {
        "data_source": load_meta()["source"],
        "candle_minutes": step,
        "total_dummy_trades": len(allt),
        "win_rate_pct_all": rate(allt, "is_profit"),
        "avg_roi_pct_all": float(allt["roi_pct"].mean()),
        "high_profit_trades": len(high),
        "high_profit_rate_pct": rate(allt, "is_high_profit"),
        "big_loss_trades": len(loss),
        "big_loss_rate_pct": rate(allt, "is_big_loss"),
        # Look-back: RSI zone share in each group (compare the three numbers!)
        "buy_rsi_in_zone_pct_ALL": pct(allt, "buy_rsi", RSI_BUY_ZONE),
        "buy_rsi_in_zone_pct_HIGH": pct(high, "buy_rsi", RSI_BUY_ZONE),
        "buy_rsi_in_zone_pct_LOSS": pct(loss, "buy_rsi", RSI_BUY_ZONE),
        "sell_rsi_in_zone_pct_ALL": pct(allt, "sell_rsi", RSI_SELL_ZONE),
        "sell_rsi_in_zone_pct_HIGH": pct(high, "sell_rsi", RSI_SELL_ZONE),
        "sell_rsi_in_zone_pct_LOSS": pct(loss, "sell_rsi", RSI_SELL_ZONE),
        # Rule test: only trades whose buy RSI was 20-30
        "rule_buy_zone_trades": len(rule_buy),
        "rule_buy_zone_win_rate_pct": rate(rule_buy, "is_profit"),
        "rule_buy_zone_avg_roi_pct": float(rule_buy["roi_pct"].mean()) if len(rule_buy) else float("nan"),
        "rule_buy_zone_high_profit_rate_pct": rate(rule_buy, "is_high_profit"),
        "rule_buy_and_sell_zone_trades": len(rule_both),
        "rule_buy_and_sell_zone_avg_roi_pct": float(rule_both["roi_pct"].mean()) if len(rule_both) else float("nan"),
        "median_rel_volume_buy_ALL": float(allt["buy_relvolume"].median()),
        "median_rel_volume_buy_HIGH": float(high["buy_relvolume"].median()) if len(high) else float("nan"),
        "median_rel_volume_buy_LOSS": float(loss["buy_relvolume"].median()) if len(loss) else float("nan"),
        "median_rel_volume_sell_ALL": float(allt["sell_relvolume"].median()),
        "median_rel_volume_sell_HIGH": float(high["sell_relvolume"].median()) if len(high) else float("nan"),
        "median_rel_liquidity_buy_ALL": float(allt["buy_relliquidity"].median()),
        "median_rel_liquidity_buy_HIGH": float(high["buy_relliquidity"].median()) if len(high) else float("nan"),
        "median_rel_liquidity_sell_ALL": float(allt["sell_relliquidity"].median()),
        "median_rel_liquidity_sell_HIGH": float(high["sell_relliquidity"].median()) if len(high) else float("nan"),
        "avg_rsi_buy_ALL": float(allt["buy_rsi"].mean()),
        "avg_rsi_buy_HIGH": float(high["buy_rsi"].mean()) if len(high) else float("nan"),
        "avg_rsi_sell_ALL": float(allt["sell_rsi"].mean()),
        "avg_rsi_sell_HIGH": float(high["sell_rsi"].mean()) if len(high) else float("nan"),
    }
    pd.Series(summary).to_csv(OUT_DIR / "summary_stats.csv", header=["value"])
    for k, v in summary.items():
        print(f"  {k:40s} {v:.2f}" if isinstance(v, float) else f"  {k:40s} {v}")

    # ---- charts ----
    for old in OUT_DIR.glob("chart3_*.png"):
        old.unlink(missing_ok=True)

    # Only PROFIT trades are charted. The grey dashed line = mean of all trades (baseline).
    charts.roi_histogram(allt["roi_pct"], HIGH_PROFIT_PCT, OUT_DIR / "chart3_1_roi_profit_trades.png")

    hp = f"+{HIGH_PROFIT_PCT:g}% trades"
    charts.profit_histogram(high["buy_rsi"], f"RSI at BUY time ({hp})", "RSI",
                            OUT_DIR / "chart3_2_buy_rsi.png", charts.BLUE,
                            all_mean=float(allt["buy_rsi"].mean()), zone=RSI_BUY_ZONE)
    charts.profit_histogram(high["sell_rsi"], f"RSI at SELL time ({hp})", "RSI",
                            OUT_DIR / "chart3_3_sell_rsi.png", charts.RED,
                            all_mean=float(allt["sell_rsi"].mean()), zone=RSI_SELL_ZONE)
    # Volume and liquidity: supervisor asked to CHECK them (11:04-11:23), histograms were only asked
    # for the patterns (10:25). So volume / liquidity are reported as numbers in summary_stats.csv
    # and in the report tables, without histograms.
    charts.grouped_bars(
        [f"Buy RSI in {RSI_BUY_ZONE[0]}-{RSI_BUY_ZONE[1]}", f"Sell RSI in {RSI_SELL_ZONE[0]}-{RSI_SELL_ZONE[1]}"],
        [([summary["buy_rsi_in_zone_pct_ALL"], summary["sell_rsi_in_zone_pct_ALL"]], "All trades (baseline)", charts.GREY),
         ([summary["buy_rsi_in_zone_pct_HIGH"], summary["sell_rsi_in_zone_pct_HIGH"]], hp, charts.GREEN)],
        f"RSI zone share: {hp} vs all trades", "% of trades in group",
        OUT_DIR / "chart3_4_rsi_zone_vs_baseline.png")
    charts.grouped_bars(
        ["Win rate %", f"+{HIGH_PROFIT_PCT:g}% rate %", "Avg ROI %"],
        [([summary["win_rate_pct_all"], summary["high_profit_rate_pct"], summary["avg_roi_pct_all"]],
          "All random trades", charts.GREY),
         ([summary["rule_buy_zone_win_rate_pct"], summary["rule_buy_zone_high_profit_rate_pct"],
           summary["rule_buy_zone_avg_roi_pct"]], f"Buy only when RSI {RSI_BUY_ZONE[0]}-{RSI_BUY_ZONE[1]}",
          charts.BLUE)],
        "Rule test: does buying at RSI 20-30 beat random buying?", "Value",
        OUT_DIR / "chart3_5_rsi_rule_test.png")

    print(f"Saved: {ENRICHED_CSV.name}, summary_stats.csv, chart3_*.png")
    print("STEP 3 DONE")


if __name__ == "__main__":
    main()
