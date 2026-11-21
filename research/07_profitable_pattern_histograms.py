"""
STEP 7 — The supervisor's core histogram, nothing else:

    all trades  ->  keep the profitable trades  ->  group them by their candle pattern
                ->  histogram: how many profitable trades had each pattern

Pattern = the 3 (or 7) candles just BEFORE the buy (or sell), each candle's close vs the previous
close: U = up, S = same (within +-0.025%), D = down.

Groups:
    Method 1 (random trades): profitable = ROI > 0, and high-profit = ROI +10% or more
    Method 2 (RSI rule trades): profitable = ROI > 0

3-candle charts show ALL 27 patterns (including ones with 0 trades).
7-candle charts show the 20 most frequent of the 2,187 possible patterns.
Output: output/supervisor_histograms/*.png, *.csv and Profitable_pattern_histograms.pdf
"""
from __future__ import annotations

import itertools
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

import charts
from config import HIGH_PROFIT_PCT, OUT_DIR, SAME_TOL, STRATEGY_TRADES_CSV, load_meta

HIST_DIR = OUT_DIR / "supervisor_histograms"
HP = f"+{HIGH_PROFIT_PCT:g}%"
ALL_3 = ["-".join(p) for p in itertools.product("USD", repeat=3)]   # all 27 patterns


def pattern_hist(patterns: pd.Series, n_group: int, title: str, out, color: str, top: int | None,
                 levels: pd.DataFrame | None = None) -> pd.DataFrame:
    """levels (optional): per pattern, median relative volume / liquidity of these trades
    -> shown as High / Normal / Low under each bar."""
    counts = patterns.value_counts()
    if top is None:                                   # 3 candles: show every pattern, even 0
        counts = counts.reindex(ALL_3, fill_value=0)
    counts = counts.sort_values(ascending=False)
    if top is not None:
        counts = counts.head(top)
    table = pd.DataFrame({"profitable_trades": counts,
                          "share_of_profitable_pct": (counts / max(n_group, 1) * 100).round(2)})

    if levels is not None:
        table["median_rel_volume"] = levels["rel_volume"].reindex(counts.index).round(3)
        table["median_rel_liquidity"] = levels["rel_liquidity"].reindex(counts.index).round(3)
        table["volume_level"] = table["median_rel_volume"].map(charts.level)
        table["liquidity_level"] = table["median_rel_liquidity"].map(charts.level)
        texts = [f"{c}\n{p:.1f}%" for c, p in zip(counts.values, table["share_of_profitable_pct"])]
        charts.bars_with_levels(list(counts.index), list(counts.values), texts,
                                list(table["volume_level"]), list(table["liquidity_level"]),
                                f"{title}  (n = {n_group:,} profitable trades)", "Number of profitable trades",
                                "Pattern of the previous candles (U = up, S = same, D = down)", out, color)
        return table

    fig, ax = plt.subplots(figsize=(12, 5.2))
    x = np.arange(len(counts))
    ax.bar(x, counts.values, color=color, edgecolor="white", width=0.75)
    for i, (c, pct) in enumerate(zip(counts.values, table["share_of_profitable_pct"])):
        ax.text(i, c, f"{c}\n{pct:.1f}%", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels(counts.index, rotation=60, ha="right", fontsize=8 if top is None else 7)
    ax.set_ylim(0, max(counts.max(), 1) * 1.2)
    ax.set_ylabel("Number of profitable trades")
    ax.set_xlabel("Pattern of the previous candles (U = up, S = same, D = down)")
    ax.set_title(f"{title}  (n = {n_group:,} profitable trades)", fontsize=11)
    ax.grid(axis="y", alpha=0.25)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return table


def main() -> None:
    print("STEP 7: Histograms of profitable trades grouped by pattern...")
    HIST_DIR.mkdir(exist_ok=True)
    for old in HIST_DIR.glob("*.png"):
        old.unlink()

    m1 = pd.read_csv(OUT_DIR / "trades_with_patterns.csv")
    m2 = pd.read_csv(STRATEGY_TRADES_CSV)
    groups = [
        ("M1_profit", "Method 1 (random)", "ROI > 0", m1[m1["roi_pct"] > 0], len(m1), "#4C78A8"),
        ("M1_plus10", "Method 1 (random)", f"ROI {HP} or more", m1[m1["is_high_profit"]], len(m1), "#54A24B"),
        ("M2_profit", "Method 2 (RSI rule)", "ROI > 0", m2[m2["roi_pct"] > 0], len(m2), "#F58518"),
    ]

    pages, summary = [], []
    for key, method, label, g, n_all, color in groups:
        for side in ("buy", "sell"):
            for L in (3, 7):
                top = None if L == 3 else 20
                name = f"{key}_{side}_{L}candle"
                title = (f"{method}, {label}: previous {L} candles before the {side.upper()}"
                         + ("" if top is None else " (top 20)"))
                levels = None
                if key == "M1_plus10":     # +10% histograms: also show volume / liquidity level
                    lv = g.groupby(f"{side}_pattern_{L}")[[f"{side}_relvolume", f"{side}_relliquidity"]].median()
                    levels = lv.rename(columns={f"{side}_relvolume": "rel_volume",
                                                f"{side}_relliquidity": "rel_liquidity"})
                tab = pattern_hist(g[f"{side}_pattern_{L}"].dropna(), len(g), title,
                                   HIST_DIR / f"{name}.png", color, top, levels)
                tab.to_csv(HIST_DIR / f"{name}.csv", index_label="pattern")
                pages.append((f"{name}.png", title))
        top_b = g["buy_pattern_3"].value_counts()
        top_s = g["sell_pattern_3"].value_counts()
        summary.append([method, label.replace(" or more", "+").replace("ROI ", ""), f"{len(g):,} of {n_all:,}", f"{len(g) / n_all * 100:.1f}%",
                        f"{top_b.index[0]} ({top_b.iloc[0]})", f"{top_s.index[0]} ({top_s.iloc[0]})"])
        print(f"  {method} {label}: {len(g):,} profitable trades | most common before buy: "
              f"{top_b.index[0]} ({top_b.iloc[0]}), before sell: {top_s.index[0]} ({top_s.iloc[0]})")

    # ---- small PDF with only these histograms ----
    meta = load_meta()
    pdf_path = HIST_DIR / "Profitable_pattern_histograms.pdf"
    with PdfPages(pdf_path) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.07, 0.95, "Profitable trades grouped by candle pattern", fontsize=16, fontweight="bold", va="top")
        intro = textwrap.dedent(f"""\
            Data: BTC/USDT 5-minute candles, {meta['study_start_pkt']} to {meta['study_end_pkt']} (Pakistan time).

            Steps: (1) take all dummy trades, (2) keep only the profitable ones, (3) for each profitable trade
            read the pattern of the 3 (or 7) candles just before the buy and just before the sell,
            (4) count how many profitable trades share the same pattern -> histogram.

            Pattern letters: each candle's close compared with the previous candle's close.
            U = up, S = same (within ±{SAME_TOL * 100:.3f}%), D = down. Oldest candle first.
            3 candles = 27 possible patterns (all shown). 7 candles = 2,187 (top 20 shown).
            Bar label = number of profitable trades and their share of all profitable trades.

            {HP} histograms: the strip under the bars shows the typical Volume and Liquidity of those
            trades at buy (or sell) time, compared with normal for that day: High = at least
            {charts.LEVEL_HIGH:g}x normal, Low = at most {charts.LEVEL_LOW:g}x normal, otherwise Normal.""")
        y = 0.89
        for line in intro.split("\n"):
            for w in textwrap.wrap(line, 100) or [""]:
                fig.text(0.07, y, w, fontsize=9.5, va="top")
                y -= 0.018
        ax = fig.add_axes([0.07, y - 0.16, 0.86, 0.14])
        ax.axis("off")
        t = ax.table(cellText=summary, colLabels=["Method", "Profitable =", "Profitable trades", "Share",
                                                  "Top pattern before BUY", "Top pattern before SELL"],
                     loc="upper left", cellLoc="left", colWidths=[0.2, 0.14, 0.17, 0.09, 0.2, 0.2])
        t.auto_set_font_size(False)
        t.set_fontsize(8)
        t.scale(1, 1.4)
        note = ("Note (Method 2): trades bought in the same dip are often sold at the same candle, "
                "so sell-pattern counts include repeats of the same moment.")
        for k, w in enumerate(textwrap.wrap(note, 105)):
            fig.text(0.07, y - 0.2 - k * 0.016, w, fontsize=8.5, style="italic")
        pdf.savefig(fig)
        plt.close(fig)

        for i in range(0, len(pages), 2):
            fig = plt.figure(figsize=(8.27, 11.69))
            for j, (fname, title) in enumerate(pages[i:i + 2]):
                ax = fig.add_axes([0.04, 0.52 - j * 0.47, 0.92, 0.44])
                ax.imshow(mpimg.imread(HIST_DIR / fname))
                ax.axis("off")
            pdf.savefig(fig)
            plt.close(fig)

    print(f"Saved: {HIST_DIR}/*.png, *.csv, {pdf_path.name}")
    print("STEP 7 DONE")


if __name__ == "__main__":
    main()
