"""Small chart helpers shared by steps 3 and 4 (clean, simple academic style)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11, "axes.titlesize": 13,
    "axes.labelsize": 11, "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.grid": True, "grid.alpha": 0.25,
    "axes.spines.top": False, "axes.spines.right": False,
})

BLUE, GREEN, RED, GREY = "#4C78A8", "#54A24B", "#E45756", "#9D9D9D"


def roi_histogram(roi: pd.Series, high: float, out: Path) -> None:
    """Profit trades only (ROI > 0) with the high-profit line."""
    data = roi.replace([np.inf, -np.inf], np.nan).dropna()
    data = data[data > 0]
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    ax.hist(data, bins=60, color=BLUE, edgecolor="white", linewidth=0.4)
    ax.axvline(high, color=GREEN, linestyle=":", linewidth=1.6, label=f"+{high:g}% (high profit)")
    ax.axvline(data.mean(), color="#222222", linestyle="--", linewidth=1.2,
               label=f"Mean = {data.mean():.2f}%")
    ax.set_title(f"ROI of profit trades (n={len(data):,})")
    ax.set_xlabel("ROI %  = (Sell / Buy) x 100 - 100")
    ax.set_ylabel("Number of trades")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def profit_histogram(series: pd.Series, title: str, xlabel: str, out: Path, color: str,
                     all_mean: float | None = None, zone: tuple[float, float] | None = None,
                     clip_pct: float | None = None) -> None:
    """One histogram for the high-profit trades only.
    Dashed line = mean of ALL trades (baseline, for comparison)."""
    data = series.replace([np.inf, -np.inf], np.nan).dropna()
    if clip_pct and len(data):
        data = data.clip(upper=data.quantile(clip_pct))
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    if len(data):
        ax.hist(data, bins=30, color=color, edgecolor="white", linewidth=0.6)
        ax.axvline(data.mean(), color="#222222", linestyle="-", linewidth=1.4,
                   label=f"Mean (these trades) = {data.mean():.2f}")
    if all_mean is not None:
        ax.axvline(all_mean, color=GREY, linestyle="--", linewidth=1.4,
                   label=f"Mean (all trades) = {all_mean:.2f}")
    if zone:
        ax.axvspan(zone[0], zone[1], color="#F58518", alpha=0.15, label=f"Zone {zone[0]}-{zone[1]}")
    ax.set_title(f"{title} (n={len(data):,})")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Number of trades")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def compare_histogram(groups: list[tuple[pd.Series, str, str]], title: str, xlabel: str,
                      out: Path, zone: tuple[float, float] | None = None,
                      clip_pct: float | None = None) -> None:
    """Same variable for several groups (All vs high-profit vs loss), as % of each group,
    so groups of very different size can be compared fairly."""
    cleaned = [(s.replace([np.inf, -np.inf], np.nan).dropna(), lab, col) for s, lab, col in groups]
    all_vals = pd.concat([s for s, _, _ in cleaned])
    hi = all_vals.quantile(clip_pct) if clip_pct else all_vals.max()
    lo = all_vals.min()
    bins = np.linspace(lo, hi, 41)
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    for s, lab, col in cleaned:
        if len(s) == 0:
            continue
        w = np.full(len(s), 100.0 / len(s))
        ax.hist(s.clip(upper=hi), bins=bins, weights=w, histtype="step", linewidth=2,
                color=col, label=f"{lab} (n={len(s):,}, mean={s.mean():.2f})")
    if zone:
        ax.axvspan(zone[0], zone[1], color="#F58518", alpha=0.12, label=f"Zone {zone[0]}-{zone[1]}")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("% of trades in group")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def grouped_bars(categories: list[str], series: list[tuple[list[float], str, str]],
                 title: str, ylabel: str, out: Path) -> None:
    x = np.arange(len(categories))
    w = 0.8 / len(series)
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    for i, (vals, lab, col) in enumerate(series):
        bars = ax.bar(x + (i - (len(series) - 1) / 2) * w, vals, w, color=col, label=lab,
                      edgecolor="white")
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.1f}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def pattern_bars(df: pd.DataFrame, value_col: str, base: float, title: str, ylabel: str,
                 out: Path, color: str) -> None:
    """Bar per pattern + dashed line = rate for ALL trades (the baseline)."""
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    if len(df):
        x = np.arange(len(df))
        ax.bar(x, df[value_col], color=color, edgecolor="white", width=0.7)
        ax.set_xticks(x)
        ax.set_xticklabels(df.index, rotation=35, ha="right", fontsize=8)
        for i, (v, c) in enumerate(zip(df[value_col], df["total"])):
            ax.text(i, v, f"{v:.1f}%\nn={c}", ha="center", va="bottom", fontsize=7)
    else:
        ax.text(0.5, 0.5, "Not enough data", ha="center", transform=ax.transAxes)
    ax.axhline(base, color="#222222", linestyle="--", linewidth=1.2,
               label=f"All trades = {base:.1f}%")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


# ---- Volume / liquidity level (High / Normal / Low) shown under pattern bars ----
LEVEL_HIGH, LEVEL_LOW = 1.2, 0.8          # relative to that day's normal (1.0)
LEVEL_COLORS = {"High": "#E45756", "Normal": "#D9D9D9", "Low": "#4C78A8", "-": "#F2F2F2"}


def level(rel_value) -> str:
    """Relative volume/liquidity (1.0 = normal for that day) -> High / Normal / Low."""
    if rel_value is None or pd.isna(rel_value):
        return "-"
    if rel_value >= LEVEL_HIGH:
        return "High"
    if rel_value <= LEVEL_LOW:
        return "Low"
    return "Normal"


def bars_with_levels(labels: list[str], heights: list[float], bar_texts: list[str],
                     vol_levels: list[str], liq_levels: list[str], title: str, ylabel: str,
                     xlabel: str, out: Path, color: str, figsize=(12, 6.4)) -> None:
    """Bar chart with a 2-row strip under the bars: Volume level and Liquidity level per bar."""
    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(2, 1, height_ratios=[5, 1.0], hspace=0.06)
    ax = fig.add_subplot(gs[0])
    st = fig.add_subplot(gs[1], sharex=ax)
    x = np.arange(len(labels))
    if len(labels):
        ax.bar(x, heights, color=color, edgecolor="white", width=0.75)
        for i, (h, t) in enumerate(zip(heights, bar_texts)):
            ax.text(i, h, t, ha="center", va="bottom", fontsize=7)
        ax.set_ylim(0, max(max(heights), 1) * 1.22)
    else:
        ax.text(0.5, 0.5, "Not enough data", ha="center", transform=ax.transAxes)
    ax.set_title(title, fontsize=11)
    ax.set_ylabel(ylabel)
    ax.tick_params(labelbottom=False)
    ax.grid(axis="x", visible=False)

    for i, (v, l) in enumerate(zip(vol_levels, liq_levels)):
        for yrow, lvl in ((1, v), (0, l)):
            st.add_patch(plt.Rectangle((i - 0.45, yrow - 0.42), 0.9, 0.84,
                                       color=LEVEL_COLORS.get(lvl, "#F2F2F2"), lw=0))
            st.text(i, yrow, lvl, ha="center", va="center", fontsize=5.4 if len(labels) > 12 else 6.5,
                    color="white" if lvl in ("High", "Low") else "black", fontweight="bold")
    st.set_ylim(-0.6, 1.6)
    st.set_yticks([1, 0])
    st.set_yticklabels(["Volume", "Liquidity"], fontsize=8.5)
    st.set_xticks(x)
    st.set_xticklabels(labels, rotation=60, ha="right", fontsize=7.5)
    st.set_xlim(-0.6, max(len(labels) - 0.4, 0.4))
    st.grid(False)
    for s in ("top", "right", "left"):
        st.spines[s].set_visible(False)
    st.set_xlabel(xlabel, fontsize=9)
    handles = [plt.Rectangle((0, 0), 1, 1, color=LEVEL_COLORS[k]) for k in ("High", "Normal", "Low")]
    ax.legend(handles, [f"High (≥{LEVEL_HIGH:g}x normal)", "Normal", f"Low (≤{LEVEL_LOW:g}x normal)"],
              title="Volume / liquidity level (typical for these trades)", title_fontsize=8, fontsize=8,
              frameon=False, loc="upper right")
    fig.savefig(out, dpi=160, bbox_inches="tight")
    plt.close(fig)


def repeat_bars(df: pd.DataFrame, n_profit: int, title: str, out: Path,
                vol_levels: list[str] | None = None, liq_levels: list[str] | None = None) -> None:
    """How many successful trades had each pattern (most repeated first).
    Label = count, share of all successful trades, and the pattern's success rate.
    If vol_levels / liq_levels are given, a Volume / Liquidity level strip is drawn under the bars."""
    if vol_levels is not None and liq_levels is not None:
        texts = [f"{int(r['high'])} ({r['share_of_profit_trades_pct']:.1f}%)\nrate {r['high_rate_pct']:.1f}%"
                 for _, r in df.iterrows()]
        bars_with_levels(list(df.index), list(df["high"]), texts, vol_levels, liq_levels,
                         f"{title} (n={n_profit:,})", "Number of successful trades",
                         "Pattern of the previous candles (U = up, S = same, D = down)", out, BLUE,
                         figsize=(10.5, 6.0))
        return
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    if len(df):
        x = np.arange(len(df))
        ax.bar(x, df["high"], color=BLUE, edgecolor="white", width=0.7)
        ax.set_xticks(x)
        ax.set_xticklabels(df.index, rotation=35, ha="right", fontsize=8)
        for i, (_, r) in enumerate(df.iterrows()):
            ax.text(i, r["high"], f"{int(r['high'])} ({r['share_of_profit_trades_pct']:.1f}%)\n"
                                  f"rate {r['high_rate_pct']:.1f}%", ha="center", va="bottom", fontsize=7)
        ax.set_ylim(0, df["high"].max() * 1.25)
    else:
        ax.text(0.5, 0.5, "Not enough data", ha="center", transform=ax.transAxes)
    ax.set_title(f"{title} (n={n_profit:,})")
    ax.set_ylabel("Number of successful trades")
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def count_bars(counts: pd.Series, title: str, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 4.8))
    x = np.arange(len(counts))
    ax.bar(x, counts.values, color=BLUE, edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels(counts.index, rotation=60, ha="right", fontsize=7)
    ax.set_title(title)
    ax.set_ylabel("Number of trades")
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
