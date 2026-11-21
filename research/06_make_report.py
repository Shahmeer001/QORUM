"""
STEP 6 — Build output/QUORUM_report.pdf for the supervisor from the results of steps 1-5.
Method 1 = random dummy trades (steps 2-4). Method 2 = RSI rule dummy trades (step 5).
Every number in the report is read from the output files, so the report always matches the run.
"""
from __future__ import annotations

import textwrap
from datetime import date

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from config import (HIGH_PROFIT_PCT, MAX_HOLD_MINUTES, MIN_HOLD_MINUTES, MIN_PATTERN_COUNT, OUT_DIR,
                    REPORT_PDF, RSI_BUY_ZONE, RSI_SELL_ZONE, SAME_TOL, SEED, STRATEGY_SUMMARY_CSV,
                    load_meta)

REPORT_AUTHOR = "Muhammad Subhan Rauf"   # change if needed
A4 = (8.27, 11.69)
HP = f"+{HIGH_PROFIT_PCT:g}%"


def page(pdf, title: str):
    fig = plt.figure(figsize=A4)
    fig.text(0.07, 0.95, title, fontsize=16, fontweight="bold", va="top")
    fig.add_artist(plt.Line2D([0.07, 0.93], [0.925, 0.925], color="#999999", lw=0.8))
    return fig


def write(fig, y: float, text: str, size: float = 10, bold: bool = False, width: int = 95,
          color: str = "black") -> float:
    """Write wrapped text starting at height y; returns the next free y."""
    for para in text.split("\n"):
        lines = textwrap.wrap(para, width=width) or [""]
        for line in lines:
            fig.text(0.07, y, line, fontsize=size, fontweight="bold" if bold else "normal",
                     va="top", color=color)
            y -= size * 0.0017
        y -= size * 0.0006
    return y


def table(fig, y: float, rows: list[list], header: list[str], col_w: list[float], height: float = 0.022) -> float:
    h = height * (len(rows) + 1)
    ax = fig.add_axes([0.07, y - h, 0.86, h])
    ax.axis("off")
    t = ax.table(cellText=rows, colLabels=header, colWidths=col_w, loc="upper left", cellLoc="left")
    t.auto_set_font_size(False)
    t.set_fontsize(8.5)
    for (r, _), cell in t.get_celld().items():
        cell.set_edgecolor("#BBBBBB")
        if r == 0:
            cell.set_facecolor("#E8EEF5")
            cell.set_text_props(fontweight="bold")
    t.scale(1, 1.25)
    return y - h - 0.025


def chart_page(pdf, title: str, items: list[tuple[str, str]]):
    fig = page(pdf, title)
    slots = [(0.07, 0.50, 0.86, 0.40), (0.07, 0.05, 0.86, 0.40)]
    for (name, caption), (x, y, w, h) in zip(items, slots):
        path = OUT_DIR / name
        if not path.exists():
            continue
        ax = fig.add_axes([x, y + 0.03, w, h - 0.03])
        ax.imshow(mpimg.imread(path))
        ax.axis("off")
        fig.text(x, y + 0.012, caption, fontsize=8.5, style="italic", color="#333333")
    pdf.savefig(fig)
    plt.close(fig)


def f1(x) -> str:
    return f"{float(x):.1f}"


def main() -> None:
    print("STEP 6: Building PDF report...")
    meta = load_meta()
    s = pd.read_csv(OUT_DIR / "summary_stats.csv", index_col=0)["value"]
    num = lambda k: float(s[k])
    trades = pd.read_csv(OUT_DIR / "trades_with_patterns.csv", parse_dates=["buy_time"])
    high = trades[trades["is_high_profit"]]
    rep3 = pd.read_csv(OUT_DIR / f"most_repeated_buy_patterns_3candle_plus{HIGH_PROFIT_PCT:g}.csv")
    rep7 = pd.read_csv(OUT_DIR / f"most_repeated_buy_patterns_7candle_plus{HIGH_PROFIT_PCT:g}.csv")
    st3 = pd.read_csv(OUT_DIR / "pattern_stats_buy_3candle.csv")
    st7 = pd.read_csv(OUT_DIR / "pattern_stats_buy_7candle.csv")
    _top = st3.set_index("pattern").loc[rep3.iloc[0]["pattern"]]
    top3_halves = (f"{rep3.iloc[0]['pattern']} reached {HP} in {_top['high_rate_h1']:.1f}% of trades in the first half "
                   f"and {_top['high_rate_h2']:.1f}% in the second half (baseline {float(trades['is_high_profit'].mean() * 100):.1f}%).")

    # When did the +10% trades happen? (are they spread out or from a few rallies?)
    months = high["buy_time"].dt.strftime("%b %Y").value_counts()
    weeks = high["buy_time"].dt.tz_convert(None).dt.to_period("W").value_counts()
    top2_share = weeks.head(2).sum() / max(len(high), 1) * 100
    top4_share = weeks.head(4).sum() / max(len(high), 1) * 100

    # Price chart with the high-profit buy points (shows WHEN the good trades happened)
    candles = pd.read_csv(OUT_DIR / "btc_ohlcv.csv", parse_dates=["timestamp"])
    candles = candles[~candles["is_warmup"]]
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(candles["timestamp"].dt.tz_convert("Asia/Karachi"), candles["Close"], color="#4C78A8",
            lw=0.7, label="BTC price (5-min close)")
    ax.scatter(high["buy_time"].dt.tz_convert("Asia/Karachi"), high["buy_price"], s=8, color="#E45756",
               zorder=3, label=f"Buy points of {HP} trades ({len(high)})")
    ax.set_title(f"BTC price and the buy points of the {HP} trades")
    ax.set_ylabel("Price ($)")
    ax.legend(frameon=False)
    ax.grid(alpha=0.25)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "chart5_price_and_high_profit_buys.png", dpi=160)
    plt.close(fig)

    with PdfPages(REPORT_PDF) as pdf:
        # ---------------- Page 1: method + data + key numbers ----------------
        fig = page(pdf, "QUORUM: Dummy Trades & Pattern Analysis")
        y = write(fig, 0.90, f"BTC/USDT, Binance Spot, 5-minute candles   |   {REPORT_AUTHOR}   |   "
                             f"{date.today():%d %b %Y}", 9.5, color="#444444")
        y = write(fig, y - 0.005, "Two methods of dummy trades: Method 1 = random buy/sell (pages 1-10), "
                                  f"Method 2 = RSI rule, buy at RSI {RSI_BUY_ZONE[0]}-{RSI_BUY_ZONE[1]} and sell at "
                                  f"RSI {RSI_SELL_ZONE[0]}-{RSI_SELL_ZONE[1]} (pages 11-16). Same analysis for both, at BUY and at SELL. Frequency count of every pattern: appendix (pages 17-22).",
                  9.5, True)
        y = write(fig, y - 0.01, "Method 1: random dummy trades", 12, True)
        y = write(fig, y, textwrap.dedent(f"""\
            1. Take {int(num('total_dummy_trades')):,} random dummy trades: random buy candle, random hold of {MIN_HOLD_MINUTES} min to {MAX_HOLD_MINUTES // 1440} days (seed {SEED}, no duplicate buy candles).
            2. ROI of every trade = (Sell / Buy) x 100 - 100. Buy and sell at candle close. No fees.
            3. Keep the high-profit trades (ROI {HP} or more) and look back at them.
            4. At buy and sell time note RSI(14), volume and liquidity (USDT traded), each compared with all trades.
            5. Note the previous 3 and 7 candles before each high-profit buy: each candle's close vs the previous candle's close = U (up), S (same, within ±{SAME_TOL * 100:.3f}%) or D (down). Count which patterns repeat."""), 9.5)

        y = write(fig, y - 0.01, "Data", 12, True)
        y = table(fig, y, [
            ["Source", meta["source"]],
            ["Period (Pakistan time)", f"{meta['study_start_pkt']}  to  {meta['study_end_pkt']} "
                                       f"({meta.get('study_months', '?')} months)"],
            ["Candles", f"{meta['study_candles']:,} five-minute candles, {meta['missing_candles']} missing"],
            ["Dummy trades", f"{int(num('total_dummy_trades')):,}"],
        ], ["Item", "Value"], [0.28, 0.72])

        y = write(fig, y, "Key numbers", 12, True)
        y = table(fig, y, [
            ["Win rate (ROI > 0), all random trades", f"{f1(num('win_rate_pct_all'))}%"],
            ["Average ROI, all random trades", f"{num('avg_roi_pct_all'):+.2f}%"],
            [f"High-profit trades (ROI {HP} or more)", f"{int(num('high_profit_trades')):,}  ({f1(num('high_profit_rate_pct'))}% of trades)"],
            [f"Sell RSI {RSI_SELL_ZONE[0]}-{RSI_SELL_ZONE[1]}: {HP} trades vs all trades",
             f"{f1(num('sell_rsi_in_zone_pct_HIGH'))}% vs {f1(num('sell_rsi_in_zone_pct_ALL'))}%"],
            [f"Buy RSI {RSI_BUY_ZONE[0]}-{RSI_BUY_ZONE[1]}: {HP} trades vs all trades",
             f"{f1(num('buy_rsi_in_zone_pct_HIGH'))}% vs {f1(num('buy_rsi_in_zone_pct_ALL'))}%"],
            [f"Most repeated previous-3-candle pattern before {HP}",
             f"{rep3.iloc[0]['pattern']}  ({int(rep3.iloc[0]['high'])} trades, {f1(rep3.iloc[0]['share_of_profit_trades_pct'])}%)"],
            [f"Most repeated previous-7-candle pattern before {HP}",
             f"{rep7.iloc[0]['pattern']}  ({int(rep7.iloc[0]['high'])} trades, {f1(rep7.iloc[0]['share_of_profit_trades_pct'])}%)"],
        ], ["Measure", "Result"], [0.58, 0.42])
        pdf.savefig(fig)
        plt.close(fig)

        # ---------------- Page 2: RSI / volume / liquidity ----------------
        fig = page(pdf, f"Buy & sell conditions of the {HP} trades")
        y = write(fig, 0.90, "Each value for the high-profit trades is shown next to the same value for ALL "
                             "random trades (the baseline). A difference only matters when it is clearly away "
                             "from the baseline.", 9.5)
        y = table(fig, y - 0.005, [
            ["Average RSI at buy", f1(num("avg_rsi_buy_ALL")), f1(num("avg_rsi_buy_HIGH"))],
            ["Average RSI at sell", f1(num("avg_rsi_sell_ALL")), f1(num("avg_rsi_sell_HIGH"))],
            [f"Buy RSI in {RSI_BUY_ZONE[0]}-{RSI_BUY_ZONE[1]} (% of trades)", f1(num("buy_rsi_in_zone_pct_ALL")), f1(num("buy_rsi_in_zone_pct_HIGH"))],
            [f"Sell RSI in {RSI_SELL_ZONE[0]}-{RSI_SELL_ZONE[1]} (% of trades)", f1(num("sell_rsi_in_zone_pct_ALL")), f1(num("sell_rsi_in_zone_pct_HIGH"))],
            ["Volume at buy (1.0 = normal for that day)", f"{num('median_rel_volume_buy_ALL'):.2f}", f"{num('median_rel_volume_buy_HIGH'):.2f}"],
            ["Volume at sell", f"{num('median_rel_volume_sell_ALL'):.2f}", f"{num('median_rel_volume_sell_HIGH'):.2f}"],
            ["Liquidity at buy (USDT traded, 1.0 = normal)", f"{num('median_rel_liquidity_buy_ALL'):.2f}", f"{num('median_rel_liquidity_buy_HIGH'):.2f}"],
            ["Liquidity at sell", f"{num('median_rel_liquidity_sell_ALL'):.2f}", f"{num('median_rel_liquidity_sell_HIGH'):.2f}"],
        ], ["Measure", "All trades", f"{HP} trades"], [0.56, 0.22, 0.22])

        y = write(fig, y, f"RSI rule test: buy only when RSI is {RSI_BUY_ZONE[0]}-{RSI_BUY_ZONE[1]}", 12, True)
        y = table(fig, y, [
            ["Trades", f"{int(num('total_dummy_trades')):,}", f"{int(num('rule_buy_zone_trades')):,}"],
            ["Win rate", f"{f1(num('win_rate_pct_all'))}%", f"{f1(num('rule_buy_zone_win_rate_pct'))}%"],
            ["Average ROI", f"{num('avg_roi_pct_all'):+.2f}%", f"{num('rule_buy_zone_avg_roi_pct'):+.2f}%"],
            [f"Share reaching {HP}", f"{f1(num('high_profit_rate_pct'))}%", f"{f1(num('rule_buy_zone_high_profit_rate_pct'))}%"],
        ], ["", "All random trades", f"RSI {RSI_BUY_ZONE[0]}-{RSI_BUY_ZONE[1]} buys"], [0.40, 0.30, 0.30])

        def compare(a: float, b: float) -> str:
            """a = value for high-profit trades, b = value for all trades."""
            r = a / b if b else float("nan")
            if r >= 1.1:
                return f"{r:.1f}x as common in {HP} trades as in all trades"
            if r <= 0.9:
                return f"less common in {HP} trades than in all trades ({a:.1f}% vs {b:.1f}%)"
            return f"about as common in {HP} trades as in all trades ({a:.1f}% vs {b:.1f}%)"

        vb_all, vb_high = num("median_rel_volume_buy_ALL"), num("median_rel_volume_buy_HIGH")
        vs_all, vs_high = num("median_rel_volume_sell_ALL"), num("median_rel_volume_sell_HIGH")
        y = write(fig, y, "Reading", 12, True)
        y = write(fig, y, textwrap.dedent(f"""\
            - Sell RSI {RSI_SELL_ZONE[0]}-{RSI_SELL_ZONE[1]} is {compare(num('sell_rsi_in_zone_pct_HIGH'), num('sell_rsi_in_zone_pct_ALL'))}. Part of this is automatic: when price has risen, RSI is high.
            - Buy RSI {RSI_BUY_ZONE[0]}-{RSI_BUY_ZONE[1]} is {compare(num('buy_rsi_in_zone_pct_HIGH'), num('buy_rsi_in_zone_pct_ALL'))}. Buying only in this zone changes the win rate from {f1(num('win_rate_pct_all'))}% to {f1(num('rule_buy_zone_win_rate_pct'))}%.
            - Volume at buy: {vb_high:.2f} for {HP} trades vs {vb_all:.2f} for all trades; at sell: {vs_high:.2f} vs {vs_all:.2f} (1.0 = normal for that day)."""), 9.5)
        pdf.savefig(fig)
        plt.close(fig)

        # ---------------- Page 3: patterns ----------------
        fig = page(pdf, f"Previous-candle patterns before the BUY of {HP} trades")
        y = write(fig, 0.90, f"Pattern = the candles BEFORE the buy candle, oldest to newest. Each letter compares that "
                             f"candle's close with the previous candle's close: U = up, S = same (within "
                             f"±{SAME_TOL * 100:.3f}%), D = down. 3 options per candle: 3 candles = 27 patterns, "
                             f"7 candles = 2,187. 'Times' = how many {HP} trades had the pattern; 'rate' = of all "
                             f"trades with that pattern, the % that reached {HP} (baseline {f1(num('high_profit_rate_pct'))}%).", 9.5)

        def rows(df, n):
            return [[r["pattern"], int(r["high"]), f"{r['share_of_profit_trades_pct']:.1f}%", int(r["total"]),
                     f"{r['high_rate_pct']:.1f}%", ("yes" if r["stable_good"] else "no") if r["enough_data"] else "too few"]
                    for _, r in df.head(n).iterrows()]
        hdr = ["Pattern", f"Times in {HP}", f"Share of {HP}", "Times in all", "Rate", "Stable?"]
        w = [0.26, 0.15, 0.15, 0.15, 0.14, 0.15]
        y = write(fig, y - 0.005, "Most repeated: previous 3 candles", 11, True)
        y = table(fig, y, rows(rep3, 8), hdr, w)
        y = write(fig, y, "Most repeated: previous 7 candles", 11, True)
        y = table(fig, y, rows(rep7, 5), hdr, w)

        n_stable3 = int(st3[st3["enough_data"]]["stable_good"].sum())
        n_stable7 = int(st7[st7["enough_data"]]["stable_good"].sum())
        month_txt = ", ".join(f"{m}: {c}" for m, c in months.items())
        y = write(fig, y, "Reading", 12, True)
        write(fig, y, textwrap.dedent(f"""\
            - The most repeated pattern before {HP} trades is {rep3.iloc[0]['pattern']} (3 candles, rate {f1(rep3.iloc[0]['high_rate_pct'])}%) and {rep7.iloc[0]['pattern']} (7 candles, rate {f1(rep7.iloc[0]['high_rate_pct'])}%), vs a baseline of {f1(num('high_profit_rate_pct'))}%. A pattern can be common simply because it occurs often; the rate shows whether it actually led to {HP} more often.
            - 'Stable' = the pattern beat the baseline in both halves of the period. Stable patterns: {n_stable3} of 3-candle, {n_stable7} of 7-candle (min {MIN_PATTERN_COUNT} trades per pattern). {top3_halves}
            - With {int(st7['enough_data'].sum())} different 7-candle patterns tested, each 'stable' one rests on only a few {HP} trades, so several can pass by chance; treat them as hints only.
            - Important: the {HP} trades are concentrated in time. {top2_share:.0f}% were bought in just 2 weeks and {top4_share:.0f}% in 4 weeks (by month: {month_txt}). So these patterns describe a few market rallies and are not yet proven as general rules."""), 9.5)
        pdf.savefig(fig)
        plt.close(fig)

        # ---------------- Chart pages ----------------
        chart_page(pdf, "ROI and RSI", [
            ("chart3_1_roi_profit_trades.png", f"ROI of profit trades, with the {HP} line."),
            ("chart3_4_rsi_zone_vs_baseline.png", "Share of trades with RSI in the buy / sell zones."),
        ])
        chart_page(pdf, f"RSI of the {HP} trades", [
            ("chart3_2_buy_rsi.png", "RSI at buy time (dashed line = mean of all trades)."),
            ("chart3_3_sell_rsi.png", "RSI at sell time (dashed line = mean of all trades)."),
        ])
        chart_page(pdf, f"When did the {HP} trades happen?", [
            ("chart5_price_and_high_profit_buys.png",
             f"Red dots = buy points of {HP} trades ({top4_share:.0f}% of them were bought in just 4 weeks)."),
        ])
        chart_page(pdf, "Most repeated patterns before the BUY", [
            ("chart4_2_most_repeated_buy_3.png", f"Previous 3 candles before the buy of {HP} trades (count, share, rate)."),
            ("chart4_4_most_repeated_buy_7.png", f"Previous 7 candles before the buy of {HP} trades (count, share, rate)."),
        ])
        chart_page(pdf, "Pattern success rate and RSI rule", [
            ("chart4_1_profit_rate_buy_3.png", f"Previous-3-candle patterns with the highest {HP} rate (dashed = all trades)."),
            ("chart3_5_rsi_rule_test.png", "Buying only at RSI 20-30 vs random buying."),
        ])

        # ---------------- Method 1: patterns before the SELL ----------------
        srep3 = pd.read_csv(OUT_DIR / f"most_repeated_sell_patterns_3candle_plus{HIGH_PROFIT_PCT:g}.csv")
        srep7 = pd.read_csv(OUT_DIR / f"most_repeated_sell_patterns_7candle_plus{HIGH_PROFIT_PCT:g}.csv")
        sst3 = pd.read_csv(OUT_DIR / "pattern_stats_sell_3candle.csv")
        sst7 = pd.read_csv(OUT_DIR / "pattern_stats_sell_7candle.csv")
        fig = page(pdf, f"Previous-candle patterns before the SELL of {HP} trades")
        y = write(fig, 0.90, f"Same U/S/D patterns, but for the candles just BEFORE the sell candle. 'Times' = how many "
                             f"{HP} trades had this pattern at their sell; 'rate' = of all trades sold after this "
                             f"pattern, the % that reached {HP} (baseline {f1(num('high_profit_rate_pct'))}%).", 9.5)
        y = write(fig, y - 0.005, "Most repeated at SELL: previous 3 candles", 11, True)
        y = table(fig, y, rows(srep3, 8), hdr, w)
        y = write(fig, y, "Most repeated at SELL: previous 7 candles", 11, True)
        y = table(fig, y, rows(srep7, 5), hdr, w)
        y = write(fig, y, "Reading", 12, True)
        write(fig, y, textwrap.dedent(f"""\
            - The most repeated pattern before the sell of {HP} trades is {srep3.iloc[0]['pattern']} (3 candles: {int(srep3.iloc[0]['high'])} trades, rate {f1(srep3.iloc[0]['high_rate_pct'])}%) and {srep7.iloc[0]['pattern']} (7 candles: {int(srep7.iloc[0]['high'])} trades).
            - Stable sell patterns (above baseline in both halves, min {MIN_PATTERN_COUNT} trades): {int(sst3[sst3['enough_data']]['stable_good'].sum())} of 3-candle, {int(sst7[sst7['enough_data']]['stable_good'].sum())} of 7-candle. As for the buy side, {top4_share:.0f}% of the {HP} trades were bought in 4 weeks, and 7-candle 'stable' patterns rest on only a few {HP} trades each, so these are observations, not rules yet."""), 9.5)
        pdf.savefig(fig)
        plt.close(fig)
        chart_page(pdf, "Most repeated patterns before the SELL", [
            ("chart4_6_most_repeated_sell_3.png", f"Previous 3 candles before the sell of {HP} trades (count, share, rate)."),
            ("chart4_7_most_repeated_sell_7.png", f"Previous 7 candles before the sell of {HP} trades (count, share, rate)."),
        ])

        # ================= METHOD 2: RSI rule dummy trades =================
        m = pd.read_csv(STRATEGY_SUMMARY_CSV, index_col=0)["value"]
        mv = lambda k: float(m[k])
        mrep3 = pd.read_csv(OUT_DIR / "strategy_most_repeated_buy_patterns_3candle.csv")
        mrep7 = pd.read_csv(OUT_DIR / "strategy_most_repeated_buy_patterns_7candle.csv")
        mst3 = pd.read_csv(OUT_DIR / "strategy_pattern_stats_buy_3candle.csv")
        stable3 = mst3[mst3["enough_data"] & mst3["stable_good"]].sort_values("high_rate_pct", ascending=False)
        months2 = pd.read_csv(OUT_DIR / "strategy_rsi_trades.csv", parse_dates=["buy_time"])["buy_time"] \
            .dt.strftime("%b %y").value_counts(sort=False)

        fig = page(pdf, "Method 2: RSI rule dummy trades")
        y = write(fig, 0.90, "Method", 12, True)
        y = write(fig, y, textwrap.dedent(f"""\
            1. Buy at the close of EVERY candle whose RSI(14) is {RSI_BUY_ZONE[0]}-{RSI_BUY_ZONE[1]} ({int(mv('trades')):,} trades from {int(mv('separate_rsi_20_30_entries'))} separate visits to the zone).
            2. Sell at the close of the first later candle whose RSI is {RSI_SELL_ZONE[0]}-{RSI_SELL_ZONE[1]} (all {int(mv('exit_rsi_70_80')):,} trades exited this way; {int(mv('dropped_still_open_at_end'))} trades still open at the end were left out).
            3. Same ROI formula, same volume / liquidity / pattern analysis as Method 1. 'Profitable' = ROI > 0."""), 9.5)
        y = write(fig, y - 0.005, "Method 1 vs Method 2", 12, True)
        y = table(fig, y, [
            ["Trades", f"{int(mv('m1_trades')):,}", f"{int(mv('trades')):,}"],
            ["Win rate (ROI > 0)", f"{f1(mv('m1_win_rate_pct'))}%", f"{f1(mv('win_rate_pct'))}%"],
            ["Average ROI", f"{mv('m1_avg_roi_pct'):+.2f}%", f"{mv('avg_roi_pct'):+.2f}%"],
            ["Median ROI", f"{mv('m1_median_roi_pct'):+.2f}%", f"{mv('median_roi_pct'):+.2f}%"],
            ["Average profit of winning trades", f"{mv('m1_avg_profit_of_winners_pct'):+.2f}%", f"{mv('avg_profit_of_winners_pct'):+.2f}%"],
            ["Average loss of losing trades", f"{mv('m1_avg_loss_of_losers_pct'):+.2f}%", f"{mv('avg_loss_of_losers_pct'):+.2f}%"],
            ["Median holding time", f"{mv('m1_median_hold_hours'):.0f} h", f"{mv('median_hold_hours'):.0f} h"],
            [f"Trades reaching {HP}", f"{int(num('high_profit_trades'))}", f"{int(mv('trades_plus10'))} (best {mv('best_trade_pct'):+.1f}%)"],
        ], ["", "Method 1: random", "Method 2: RSI rule"], [0.44, 0.28, 0.28])

        y = write(fig, y, "Volume and liquidity of the profitable RSI-rule trades", 12, True)
        y = table(fig, y, [
            ["Volume at buy (1.0 = normal for that day)", f"{mv('median_rel_volume_buy_ALL'):.2f}", f"{mv('median_rel_volume_buy_PROFIT'):.2f}"],
            ["Volume at sell", f"{mv('median_rel_volume_sell_ALL'):.2f}", f"{mv('median_rel_volume_sell_PROFIT'):.2f}"],
            ["Liquidity at buy (USDT traded)", f"{mv('median_rel_liquidity_buy_ALL'):.2f}", f"{mv('median_rel_liquidity_buy_PROFIT'):.2f}"],
            ["Liquidity at sell", f"{mv('median_rel_liquidity_sell_ALL'):.2f}", f"{mv('median_rel_liquidity_sell_PROFIT'):.2f}"],
        ], ["Median", "All RSI-rule trades", "Profitable RSI-rule trades"], [0.44, 0.28, 0.28])

        y = write(fig, y, "Reading", 12, True)
        write(fig, y, textwrap.dedent(f"""\
            - The RSI rule wins more often ({f1(mv('win_rate_pct'))}% vs {f1(mv('m1_win_rate_pct'))}%), but the average ROI is only {mv('avg_roi_pct'):+.2f}% (random: {mv('m1_avg_roi_pct'):+.2f}%): wins are small ({mv('avg_profit_of_winners_pct'):+.2f}%) and losses are {abs(mv('avg_loss_of_losers_pct')) / max(mv('avg_profit_of_winners_pct'), 1e-9):.1f}x as big ({mv('avg_loss_of_losers_pct'):+.2f}%, worst {mv('worst_trade_pct'):+.1f}%).
            - Trades are short (median {mv('median_hold_hours'):.0f} h) because RSI reaches 70 quickly on 5-minute candles, so {int(mv('trades_plus10'))} trades reached {HP} (best {mv('best_trade_pct'):+.1f}%).
            - At RSI {RSI_BUY_ZONE[0]}-{RSI_BUY_ZONE[1]} the volume is already about {mv('median_rel_volume_buy_ALL'):.1f}x normal (price falls on high volume). Volume at sell: {mv('median_rel_volume_sell_PROFIT'):.2f} for profitable trades vs {mv('median_rel_volume_sell_ALL'):.2f} for all RSI-rule trades.
            - Unlike Method 1, these trades are spread over all months ({', '.join(f'{k}: {v}' for k, v in months2.items())})."""), 9.5)
        pdf.savefig(fig)
        plt.close(fig)

        fig = page(pdf, "Method 2: patterns before the BUY")
        y = write(fig, 0.90, f"Same U/S/D patterns as Method 1 (previous candles before the buy). 'Rate' = of all "
                             f"RSI-rule trades with that pattern, the % that were profitable (baseline "
                             f"{f1(mv('win_rate_pct'))}%).", 9.5)

        def rows2(df, n):
            return [[r["pattern"], int(r["times_in_profitable"]), f"{r['share_of_profit_trades_pct']:.1f}%",
                     int(r["total"]), f"{r['win_rate_pct']:.1f}%", ("yes" if r["stable_good"] else "no") if r["enough_data"] else "too few"]
                    for _, r in df.head(n).iterrows()]
        hdr2 = ["Pattern", "In profitable", "Share", "In all", "Rate", "Stable?"]
        y = write(fig, y - 0.005, "Most repeated: previous 3 candles", 11, True)
        y = table(fig, y, rows2(mrep3, 8), hdr2, w)
        y = write(fig, y, "Most repeated: previous 7 candles", 11, True)
        y = table(fig, y, rows2(mrep7, 4), hdr2, w)
        stable_txt = ", ".join(f"{r['pattern']} ({r['high_rate_pct']:.1f}%, n={int(r['total'])})"
                               for _, r in stable3.iterrows()) or "none"
        y = write(fig, y, "Reading", 12, True)
        write(fig, y, textwrap.dedent(f"""\
            - Before an RSI-rule buy the price has usually been falling, so D-heavy patterns are common. The most repeated, {mrep3.iloc[0]['pattern']}, has a rate of {f1(mrep3.iloc[0]['win_rate_pct'])}% vs the baseline of {f1(mv('win_rate_pct'))}%.
            - Stable 3-candle patterns (above baseline in both halves, min {MIN_PATTERN_COUNT} trades): {stable_txt}.
            - 7-candle patterns repeat too rarely here (top pattern only {int(mrep7.iloc[0]['times_in_profitable'])} times) to draw conclusions."""), 9.5)
        pdf.savefig(fig)
        plt.close(fig)

        # ---------------- Method 2: patterns before the SELL ----------------
        msrep3 = pd.read_csv(OUT_DIR / "strategy_most_repeated_sell_patterns_3candle.csv")
        msrep7 = pd.read_csv(OUT_DIR / "strategy_most_repeated_sell_patterns_7candle.csv")
        msst3 = pd.read_csv(OUT_DIR / "strategy_pattern_stats_sell_3candle.csv")
        mstable_s = msst3[msst3["enough_data"] & msst3["stable_good"]].sort_values("high_rate_pct", ascending=False)

        def rows3(df, n):
            return [[r["pattern"], int(r["times_in_profitable"]), f"{r['share_of_profit_trades_pct']:.1f}%",
                     int(r["total"]), int(r["unique_moments"]), f"{r['win_rate_pct']:.1f}%",
                     ("yes" if r["stable_good"] else "no") if r["enough_data"] else "too few"]
                    for _, r in df.head(n).iterrows()]
        hdr3 = ["Pattern", "In profitable", "Share", "In all", "Distinct sells", "Rate", "Stable?"]
        w3 = [0.24, 0.13, 0.11, 0.11, 0.14, 0.12, 0.15]
        fig = page(pdf, "Method 2: patterns before the SELL")
        y = write(fig, 0.90, f"Previous candles just BEFORE the sell candle (sell = first candle with RSI "
                             f"{RSI_SELL_ZONE[0]}-{RSI_SELL_ZONE[1]}). 'Rate' = of all RSI-rule trades sold after "
                             f"this pattern, the % that were profitable (baseline {f1(mv('win_rate_pct'))}%). "
                             f"'Distinct sells' = how many different sell candles are behind the count.", 9.5)
        y = write(fig, y - 0.005, "Most repeated at SELL: previous 3 candles", 11, True)
        y = table(fig, y, rows3(msrep3, 8), hdr3, w3)
        y = write(fig, y, "Most repeated at SELL: previous 7 candles", 11, True)
        y = table(fig, y, rows3(msrep7, 4), hdr3, w3)
        stable_s_txt = ", ".join(f"{r['pattern']} ({r['high_rate_pct']:.1f}%, {int(r['unique_moments'])} distinct sells)"
                                 for _, r in mstable_s.iterrows()) or "none"
        y = write(fig, y, "Reading", 12, True)
        write(fig, y, textwrap.dedent(f"""\
            - The sell happens when RSI reaches {RSI_SELL_ZONE[0]}-{RSI_SELL_ZONE[1]}, i.e. after the price has risen, so U-heavy patterns are common. Most repeated: {msrep3.iloc[0]['pattern']} ({int(msrep3.iloc[0]['times_in_profitable'])} profitable trades, rate {f1(msrep3.iloc[0]['win_rate_pct'])}%).
            - Important: trades bought in the same dip are sold at the same candle, so the {int(mv('trades')):,} trades have only {int(mv('unique_sell_candles'))} distinct sell candles. Counts on this page therefore look bigger than the real evidence (see 'Distinct sells').
            - Stable 3-candle sell patterns: {stable_s_txt}."""), 9.5)
        pdf.savefig(fig)
        plt.close(fig)

        chart_page(pdf, "Method 2: comparison and ROI", [
            ("chart6_1_random_vs_rsi_rule.png", "Method 1 (random) vs Method 2 (RSI rule)."),
            ("chart6_2_roi_profitable.png", "ROI of profitable RSI-rule trades (dashed = average of all RSI-rule trades)."),
        ])
        chart_page(pdf, "Method 2: most repeated patterns before the BUY", [
            ("chart6_3_most_repeated_buy_3.png", "Previous 3 candles before the buy of profitable RSI-rule trades."),
            ("chart6_4_most_repeated_buy_7.png", "Previous 7 candles before the buy of profitable RSI-rule trades."),
        ])
        chart_page(pdf, "Method 2: most repeated patterns before the SELL", [
            ("chart6_5_most_repeated_sell_3.png",
             f"Previous 3 candles before the sell ({int(mv('unique_sell_candles'))} distinct sell candles in total)."),
            ("chart6_6_most_repeated_sell_7.png", "Previous 7 candles before the sell of profitable RSI-rule trades."),
        ])

        # ================= APPENDIX: frequency count of every pattern =================
        hp_col = f"times_plus{HIGH_PROFIT_PCT:g}"
        hp_rate = f"plus{HIGH_PROFIT_PCT:g}_rate_pct"

        def m1_rows(df, n):
            return [[r["pattern"], int(r["times_appeared"]), int(r["times_profit"]), f"{r['profit_rate_pct']:.1f}%",
                     int(r[hp_col]), f"{r[hp_rate]:.1f}%", f"{r['avg_roi_pct']:+.2f}%"] for _, r in df.head(n).iterrows()]

        def m2_rows(df, n, side):
            return [[r["pattern"], int(r["times_appeared"]), int(r["times_profit"]), f"{r['profit_rate_pct']:.1f}%",
                     f"{r['avg_roi_pct']:+.2f}%", int(r[f"distinct_{side}_candles"])] for _, r in df.head(n).iterrows()]

        m1_hdr = ["Pattern", "Appeared", "Profit (ROI>0)", "Profit %", f"{HP}", f"{HP} %", "Avg ROI"]
        m1_w = [0.22, 0.12, 0.14, 0.12, 0.12, 0.12, 0.16]
        m2_hdr = ["Pattern", "Appeared", "Profit (ROI>0)", "Profit %", "Avg ROI", "Distinct candles"]
        m2_w = [0.24, 0.14, 0.16, 0.14, 0.14, 0.18]
        note = ("'Appeared' = how many trades had this pattern; 'Profit' = how many of them made a profit; "
                "'%' = Profit / Appeared. Sorted by how often the pattern appeared. Full lists in the CSV files.")

        for side in ("buy", "sell"):
            f3 = pd.read_csv(OUT_DIR / f"pattern_frequency_{side}_3candle.csv")
            fig = page(pdf, f"Appendix: Method 1, all 3-candle patterns before the {side.upper()}")
            y = write(fig, 0.90, f"{note} Baseline: profit {f1(num('win_rate_pct_all'))}%, {HP} "
                                 f"{f1(num('high_profit_rate_pct'))}% of all trades.", 9)
            table(fig, y - 0.005, m1_rows(f3, 27), m1_hdr, m1_w, height=0.021)
            pdf.savefig(fig)
            plt.close(fig)
        fig = page(pdf, "Appendix: Method 1, most frequent 7-candle patterns")
        y = write(fig, 0.90, f"{note} 7 candles have 2,187 possible patterns, so only the 15 most frequent are shown.", 9)
        for side in ("buy", "sell"):
            f7 = pd.read_csv(OUT_DIR / f"pattern_frequency_{side}_7candle.csv")
            y = write(fig, y - 0.005, f"Before the {side.upper()} (top 15)", 11, True)
            y = table(fig, y, m1_rows(f7, 15), m1_hdr, m1_w, height=0.0205)
        pdf.savefig(fig)
        plt.close(fig)

        for side in ("buy", "sell"):
            f3 = pd.read_csv(OUT_DIR / f"strategy_pattern_frequency_{side}_3candle.csv")
            fig = page(pdf, f"Appendix: Method 2, all 3-candle patterns before the {side.upper()}")
            y = write(fig, 0.90, f"{note} Baseline: profit {f1(mv('win_rate_pct'))}% of all RSI-rule trades. "
                                 f"'Distinct candles' = how many different {side} candles are behind the count.", 9)
            table(fig, y - 0.005, m2_rows(f3, 27, side), m2_hdr, m2_w, height=0.021)
            pdf.savefig(fig)
            plt.close(fig)
        fig = page(pdf, "Appendix: Method 2, most frequent 7-candle patterns")
        y = write(fig, 0.90, f"{note} Only the 15 most frequent are shown.", 9)
        for side in ("buy", "sell"):
            f7 = pd.read_csv(OUT_DIR / f"strategy_pattern_frequency_{side}_7candle.csv")
            y = write(fig, y - 0.005, f"Before the {side.upper()} (top 15)", 11, True)
            y = table(fig, y, m2_rows(f7, 15, side), m2_hdr, m2_w, height=0.0205)
        pdf.savefig(fig)
        plt.close(fig)

        # ---------------- Last page ----------------
        fig = page(pdf, "Limitations, next steps, questions")
        y = write(fig, 0.90, "Limitations", 12, True)
        y = write(fig, y, textwrap.dedent(f"""\
            - Look-back analysis on historical data with dummy trades; no fees or slippage (about 0.2% per round trip on Binance). With fees, the small RSI-rule wins would mostly disappear.
            - Trades overlap in time, so they are observations, not a portfolio.
            - Method 1: {top4_share:.0f}% of the {HP} trades were bought in just 4 weeks (a few rallies), so pattern results are observations, not rules yet.
            - Method 2: high win rate ({f1(mv('win_rate_pct'))}%) but average ROI only {mv('avg_roi_pct'):+.2f}%, which fees (about 0.2%) would erase; large losses when price keeps falling after RSI 20-30."""), 9.5)
        y = write(fig, y - 0.01, "Next steps", 12, True)
        y = write(fig, y, textwrap.dedent("""\
            - Give agent_pattern_knowledge.json (baseline, RSI rule, patterns) to the debating agents as evidence.
            - Run the same pipeline on other coins and a longer period to test whether the patterns hold.
            - Add fees, then move from dummy data to live data for the final presentation."""), 9.5)
        y = write(fig, y - 0.01, "Questions for the supervisor", 12, True)
        write(fig, y, textwrap.dedent(f"""\
            0. Which dummy trades did you mean: random (Method 1), RSI rule (Method 2), or both?
            1. Is the high-profit threshold of {HP} acceptable (20% gave too few trades)?
            2. Compare the close with the previous close - is this the comparison you meant?
            3. Is ±{SAME_TOL * 100:.3f}% a good limit for "same"?
            4. On the page: what does "7 x 3 = 21" refer to?
            5. When can we get the test-system credentials for the module?"""), 9.5)
        pdf.savefig(fig)
        plt.close(fig)

    print(f"Saved: {REPORT_PDF}")
    print("STEP 6 DONE")


if __name__ == "__main__":
    main()
