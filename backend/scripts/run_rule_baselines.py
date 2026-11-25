"""
Rule-set baseline evaluation on the VALIDATION window (2024-01-01 to 2024-12-31).

Three traders per rule set R1-R5, per target market (US, CRYPTO):
  A. Rule-following trader: takes the signal direction exactly.
  B. Rule-trigger random trader: when the rule fires (BUY or SELL), choose the
     direction uniformly at random (200 seeds). Same fills and costs.
     NOTE: uniform-random-when-triggered is a simplification. The supervisor noted
     it is "technically wrong" because a correct null model should preserve trigger
     frequency but randomise only direction; this is documented here and in
     docs/status/baseline_note.md. The result is kept as a sensitivity check.
  C. Matched-random-timing baseline: BUY/SELL/HOLD drawn uniformly at random,
     independent of whether the rule fires, 200 seeds.

All three use the SAME execution engine, fill rule, and friction as BarByBarSimulator:
  - SPY fills at the next US trading day's open.
  - BTC fills at the first 1h candle open at or after the 21:00 UTC cutoff.
  - Per-market friction from markets.yaml (US: 0.05% comm, 0.02% slip;
    CRYPTO: 0.10% comm, 0.05% slip).

Window definitions (from settings.py / protocol.md):
  - Learn   : 2022-01-03 to 2023-12-31  (knowledge built on this split)
  - Validate: 2024-01-01 to 2024-12-31  (parameters chosen here; DO NOT use test window)

Outputs a summary table to stdout and writes
  docs/status/rule_baselines_validation.md
"""
from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.settings import DATA_CACHE_DIR, INITIAL_CAPITAL, get_us_close_utc
from app.signals.rule_sets import evaluate_rule_set
from app.simulator.signal_engine import simulate_positions

# ---------------------------------------------------------------------------
# Window: VALIDATION ONLY. Do not change to 2025+.
# ---------------------------------------------------------------------------
VAL_START = "2024-01-01"
VAL_END = "2024-12-31"
LEARN_END = "2023-12-31"  # candles up to here are available to build signals
RULE_SETS = ["R1", "R2", "R3", "R4", "R5"]
N_SEEDS = 200
LOOKBACK = 50  # extra bars before val window for signal warm-up


@dataclass
class RunResult:
    rule: str
    trader: str          # "rule", "trigger_random", "timing_random"
    target: str
    seed: int            # -1 for deterministic traders
    pnl_pct: float
    max_dd_pct: float
    sharpe: float
    hit_rate_pct: float
    trade_count: int
    exposure_pct: float


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def _load_spy(spy_path: Path) -> Tuple[pd.DataFrame, Dict]:
    df = pd.read_csv(spy_path)
    df["dt"] = pd.to_datetime(
        df["Date"].astype(str).str.split().str[0], format="%d/%m/%Y"
    ).dt.date
    df = df.sort_values("dt").reset_index(drop=True)
    by_date = {row["dt"]: row for _, row in df.iterrows()}
    return df, by_date


def _load_btc(btc_path: Path) -> pd.DataFrame:
    df = pd.read_csv(btc_path)
    df["open_dt"] = pd.to_datetime(df["timestamp"])
    df["close_dt"] = df["open_dt"] + pd.Timedelta(hours=1)
    df = df.sort_values("open_dt").reset_index(drop=True)
    # pandas astype('int64') on a tz-aware series yields MICROSECONDS since epoch.
    df["close_dt_us"] = df["close_dt"].astype("int64").to_numpy()
    df["open_dt_us"]  = df["open_dt"].astype("int64").to_numpy()
    return df


def _btc_cutoff_idx(btc_df: pd.DataFrame, eval_date) -> int:
    """Index of the last BTC candle whose close_dt <= US-close cutoff (microseconds)."""
    cutoff_us = int(get_us_close_utc(eval_date.isoformat()).timestamp() * 1_000_000)
    idx = int(pd.Series(btc_df["close_dt_us"].values).searchsorted(cutoff_us, side="right")) - 1
    return idx


def _val_days_us(spy_df: pd.DataFrame) -> List:
    start = pd.to_datetime(VAL_START).date()
    end = pd.to_datetime(VAL_END).date()
    return [d for d in spy_df["dt"] if start <= d <= end]


def _btc_has_data(btc_df: pd.DataFrame, d) -> bool:
    idx = _btc_cutoff_idx(btc_df, d)
    if idx < 0:
        return False
    cutoff_us     = int(get_us_close_utc(d.isoformat()).timestamp() * 1_000_000)
    last_close_us = int(btc_df["close_dt_us"].iloc[idx])
    return (cutoff_us - last_close_us) <= 3_600_000_000   # 1 hour in microseconds


def _spy_closes_before(spy_df: pd.DataFrame, eval_date, n: int) -> List[float]:
    rows = spy_df[spy_df["dt"] <= eval_date]
    return list(rows["Close"].values[-n:])


def _btc_closes_before(btc_df: pd.DataFrame, eval_date, n: int) -> List[float]:
    idx = _btc_cutoff_idx(btc_df, eval_date)
    if idx < 0:
        return []
    start = max(0, idx - n + 1)
    return list(btc_df["Close"].values[start: idx + 1])


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _simulate_from_signals(
    target: str,
    eval_days: List,
    day_signals: Dict,       # date -> "BUY"|"SELL"|"NONE"
    spy_by_date: Dict,
    btc_df: pd.DataFrame,
    allow_short: bool = False,
    exec_raw_map: Dict = None,
    curr_close_map: Dict = None,
) -> Tuple[float, float, float, float, int, float]:
    """Execute the fill/friction loop given a pre-built {date: signal} dict."""
    """Maps signals to long/flat positions and runs the shared engine.
    BUY = long, SELL = flat, anything else keeps the position."""
    if allow_short:
        raise NotImplementedError("rule baselines are long/flat")
    if not (exec_raw_map and curr_close_map):
        raise ValueError("price maps are required")
    positions = [{"BUY": 1, "SELL": 0}.get(day_signals.get(d, "NONE")) for d in eval_days]
    perf = simulate_positions(
        target, eval_days, positions,
        [exec_raw_map[d] for d in eval_days], [curr_close_map[d] for d in eval_days],
    )
    return (perf.pnl_pct, perf.max_drawdown_pct, perf.sharpe_ratio, perf.hit_rate_pct,
            perf.trade_count, perf.exposure_pct)


def _run_all(spy_path: Path, btc_path: Path) -> List[RunResult]:
    spy_df, spy_by_date = _load_spy(spy_path)
    btc_df = _load_btc(btc_path)
    us_days = _val_days_us(spy_df)
    crypto_days = [d for d in us_days if _btc_has_data(btc_df, d)]

    results: List[RunResult] = []

    for target in ["US", "CRYPTO"]:
        days = us_days if target == "US" else crypto_days
        if not days:
            continue

        # Pre-build close arrays once per day — avoids O(n) pandas slices per call
        print(f"  Pre-building close arrays for {target} ({len(days)} days)…")
        if target == "US":
            day_closes = {d: _spy_closes_before(spy_df, d, LOOKBACK) for d in days}
        else:
            day_closes = {d: _btc_closes_before(btc_df, d, LOOKBACK) for d in days}

        # Pre-build exec_raw and curr_close for every day (avoids per-day pandas filters)
        # exec_raw = fill price (next open for US; first candle at cutoff for CRYPTO)
        # curr_close = mark-to-market price at day-end
        exec_raw_map: Dict = {}
        curr_close_map: Dict = {}
        btc_closes_arr = btc_df["Close"].values
        btc_open_arr   = btc_df["Open"].values
        btc_open_dt_us = btc_df["open_dt_us"].values

        for idx_d, d in enumerate(days):
            if target == "US":
                next_d = days[idx_d + 1] if idx_d + 1 < len(days) else None
                exec_raw_map[d] = float(spy_by_date[next_d]["Open"]) if next_d and next_d in spy_by_date \
                                   else float(spy_by_date[d]["Close"])
                curr_close_map[d] = float(spy_by_date[d]["Close"])
            else:
                cutoff_us = int(get_us_close_utc(d.isoformat()).timestamp() * 1_000_000)
                nxt_idx = int(pd.Series(btc_open_dt_us).searchsorted(cutoff_us, side="left"))
                exec_raw_map[d] = float(btc_open_arr[nxt_idx]) if nxt_idx < len(btc_open_arr) \
                                   else float(day_closes[d][-1]) if day_closes[d] else 50000.0
                close_idx = _btc_cutoff_idx(btc_df, d)
                curr_close_map[d] = float(btc_closes_arr[close_idx]) if close_idx >= 0 \
                                     else float(day_closes[d][-1]) if day_closes[d] else 50000.0

        for rule in RULE_SETS:
            # Pre-compute rule signals once
            rule_signals: Dict = {d: evaluate_rule_set(rule, day_closes[d]) for d in days}

            # A. Rule-following trader
            pnl, dd, sh, hr, tc, exp = _simulate_from_signals(
                target, days, rule_signals, spy_by_date, btc_df,
                exec_raw_map=exec_raw_map, curr_close_map=curr_close_map)
            results.append(RunResult(rule, "rule", target, -1, pnl, dd, sh, hr, tc, exp))

            # B. Rule-trigger random (200 seeds): trigger preserved, direction random
            pnl_b, dd_b, sh_b = [], [], []
            for seed in range(N_SEEDS):
                rng = random.Random(seed + 7000)
                triggered = {
                    d: (rng.choice(["BUY", "SELL"]) if rule_signals[d] != "NONE" else "NONE")
                    for d in days
                }
                p, d2, s, *_ = _simulate_from_signals(
                    target, days, triggered, spy_by_date, btc_df,
                    exec_raw_map=exec_raw_map, curr_close_map=curr_close_map)
                pnl_b.append(p); dd_b.append(d2); sh_b.append(s)
            results.append(RunResult(rule, "trigger_random_mean", target, -1,
                                     sum(pnl_b)/N_SEEDS, sum(dd_b)/N_SEEDS, sum(sh_b)/N_SEEDS, 0.0, 0, 0.0))

            # C. Matched-random-timing (200 seeds): uniform BUY/SELL/NONE, ignores rule
            pool = ["BUY", "SELL", "NONE"]
            pnl_c, dd_c, sh_c = [], [], []
            for seed in range(N_SEEDS):
                rng2 = random.Random(seed + 9000)
                timing = {d: rng2.choice(pool) for d in days}
                p, d2, s, *_ = _simulate_from_signals(
                    target, days, timing, spy_by_date, btc_df,
                    exec_raw_map=exec_raw_map, curr_close_map=curr_close_map)
                pnl_c.append(p); dd_c.append(d2); sh_c.append(s)
            results.append(RunResult(rule, "timing_random_mean", target, -1,
                                     sum(pnl_c)/N_SEEDS, sum(dd_c)/N_SEEDS, sum(sh_c)/N_SEEDS, 0.0, 0, 0.0))

    return results


def _write_report(results: List[RunResult], out_path: Path) -> None:
    lines = [
        "# Rule-Set Baselines — Validation Window (2024-01-01 to 2024-12-31)",
        "",
        "> Preliminary (FYP1). Validation window only.",
        "> Test window (2025-2026) is held out.",
        "",
        "**Note on rule-trigger random baseline**: when a rule fires, direction is chosen",
        "uniformly at random (BUY or SELL, 50/50). The supervisor noted this is technically",
        "wrong because it does not preserve the original directional bias of the rule.",
        "It is kept as a sensitivity check; the matched-random-timing baseline (C) is the",
        "primary null model.",
        "",
        "Parameters (all from `settings.py`): RSI period 14, buy<30, sell>70;",
        "MACD (12,26,9); Bollinger (20, 2 std).",
        "",
        "| Target | Rule | Trader | Return(%) | MaxDD(%) | Sharpe | Hit%(approx) | Exposure% |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r.target} | {r.rule} | {r.trader} |"
            f" {r.pnl_pct:+.2f} | {r.max_dd_pct:.2f} | {r.sharpe:.2f} |"
            f" {r.hit_rate_pct:.1f} | {r.exposure_pct:.1f} |"
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report written to {out_path}")


def main():
    spy_path = DATA_CACHE_DIR / "spy_daily.csv"
    btc_path = DATA_CACHE_DIR / "btc_1h.csv"
    results = _run_all(spy_path, btc_path)

    # Print table
    print(f"\n{'Target':<8} {'Rule':<4} {'Trader':<22} {'Return%':>8} {'MaxDD%':>7} {'Sharpe':>7}")
    print("-" * 65)
    for r in results:
        print(f"{r.target:<8} {r.rule:<4} {r.trader:<22} {r.pnl_pct:>7.2f}% {r.max_dd_pct:>6.2f}% {r.sharpe:>7.2f}")

    report_path = Path(__file__).resolve().parent.parent.parent / "docs" / "status" / "rule_baselines_validation.md"
    _write_report(results, report_path)


if __name__ == "__main__":
    main()
