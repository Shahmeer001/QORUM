"""
Validation-window mode comparison experiment.
Window: 2024-01-01 to 2024-12-31  (VALIDATION ONLY — test window never touched here).
Knowledge learned on: 2022-01-03 to 2023-12-31  (strict 2-year learn split).

Modes compared: SINGLE, SILENT_UNWEIGHTED, SILENT_WEIGHTED, DEBATE.
Both targets: US (SPY) and CRYPTO (BTC).
Two sessions per day: target=US (CRYPTO informs) and target=CRYPTO (US informs).
Reported separately; never averaged.

Baselines (same engine, fills, friction, days):
  B1: Buy-and-Hold (via BarByBarSimulator.compute_buy_and_hold)
  B2: Always-Flat  (zero exposure, equity stays flat at initial capital)
  B3: Matched-random-timing (200 seeds, uniform BUY/SELL/NONE per day)

Metrics reported per run:
  Return(%), MaxDD(%), Sharpe, HitRate(%), Exposure(%), Trades, Turnover,
  RiskVetoes, BuyHold(%), B&H-xExposure(%)

Bootstrap 95% CI on Return(%):  resample the daily_decisions PnL contributions
  with replacement, 2000 iterations.

Debate-vs-silent-weighted change analysis:
  Count days where DEBATE final_action != SILENT_WEIGHTED final_action.
  For each such day, determine whether the debate decision produced a better
  outcome (next-day return in the same direction, +1) or worse (-1).
  "Better" = final_action sign matches sign(next_close / curr_close - 1).

No parameters are tuned. All settings come from settings.py.
Runs stored in DB via persist_run when --db-path is provided.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.adapters.binance_btc import BinanceBTCAdapter
from app.adapters.us_spy import USMarketAdapter
import app.simulator.replay_simulator as replay
from app.agents.brains.rule_brain import THRESHOLDS_FILE, RuleBrain
from app.board.memory_repo import MemoryBoardRepository
from app.config.settings import DATA_CACHE_DIR, INITIAL_CAPITAL, get_us_close_utc
from app.domain.enums import Action, Mode, MsgType
from app.domain.models import EquityPoint
from app.simulator.metrics import compute_full_metrics
from app.simulator.replay_simulator import BarByBarSimulator, SimulationResult
from app.simulator.signal_engine import price_arrays, simulate_positions

# ---------------------------------------------------------------------------
# Window definitions — NEVER change these to test-window dates.
# ---------------------------------------------------------------------------
VAL_START   = "2024-01-01"
VAL_END     = "2024-12-31"
LEARN_START = "2022-01-03"
LEARN_END   = "2023-12-31"
N_BOOTSTRAP = 2000
N_RANDOM    = 200


# ---------------------------------------------------------------------------
# 1.  Build 2022-2023 knowledge into a temp directory.
# ---------------------------------------------------------------------------

def build_validation_knowledge(tmp_dir: Path) -> Path:
    """
    Builds pattern knowledge strictly from 2022-01-03 to 2023-12-31.
    Writes us.json and crypto.json to tmp_dir.
    Returns tmp_dir.
    """
    tmp_dir.mkdir(parents=True, exist_ok=True)

    from collections import defaultdict
    import hashlib

    spy_path = DATA_CACHE_DIR / "spy_daily.csv"
    btc_path = DATA_CACHE_DIR / "btc_1h.csv"
    SAME_TOL = 0.00025

    def _pattern_stats(closes, market_name: str) -> dict:
        c = np.array(closes, dtype=float)
        if len(c) < 10:
            return {}
        returns = c[1:] / c[:-1] - 1.0
        moves = np.where(returns > SAME_TOL, "U",
                         np.where(returns < -SAME_TOL, "D", "S"))
        fwd = returns[3:]
        baseline_wr = float(np.mean(fwd > 0.0) * 100.0)
        counts: Dict = defaultdict(int)
        wins:   Dict = defaultdict(int)
        for i in range(len(moves) - 3):
            pat = f"{moves[i]}-{moves[i+1]}-{moves[i+2]}"
            counts[pat] += 1
            if returns[i + 3] > 0.0:
                wins[pat] += 1
        patterns = {}
        for pat, cnt in counts.items():
            wr = (wins[pat] / cnt * 100.0) if cnt > 0 else 50.0
            patterns[pat] = {
                "count": cnt,
                "win_rate_pct": round(wr, 2),
                "lift": round(wr / baseline_wr, 4) if baseline_wr > 0 else 1.0,
            }
        return {
            "market": market_name,
            "split": {"learning_window": [LEARN_START, LEARN_END],
                      "note": "Validation-experiment knowledge: 2022-2023 only."},
            "baseline": {"total_bars": len(c), "win_rate_pct": round(baseline_wr, 2)},
            "patterns": patterns,
        }

    # SPY
    spy_df = pd.read_csv(spy_path)
    spy_df["dt"] = pd.to_datetime(spy_df["Date"].astype(str).str.split().str[0], format="%d/%m/%Y").dt.date
    learn_spy = spy_df[(spy_df["dt"] >= pd.to_datetime(LEARN_START).date()) &
                       (spy_df["dt"] <= pd.to_datetime(LEARN_END).date())]
    spy_stats = _pattern_stats(learn_spy["Close"].values, "US")
    (tmp_dir / "us.json").write_text(json.dumps(spy_stats, indent=2), encoding="utf-8")

    # BTC
    btc_df = pd.read_csv(btc_path)
    btc_df["open_dt"] = pd.to_datetime(btc_df["timestamp"])
    learn_btc = btc_df[(btc_df["open_dt"] >= pd.to_datetime(f"{LEARN_START} 00:00:00+00:00")) &
                       (btc_df["open_dt"] <= pd.to_datetime(f"{LEARN_END} 23:59:59+00:00"))]
    btc_stats = _pattern_stats(learn_btc["Close"].values, "CRYPTO")
    (tmp_dir / "crypto.json").write_text(json.dumps(btc_stats, indent=2), encoding="utf-8")

    print(f"  Validation knowledge written to {tmp_dir}  "
          f"(SPY {len(learn_spy)} bars, BTC {len(learn_btc)} bars)")
    return tmp_dir


# ---------------------------------------------------------------------------
# 2.  Validation-window simulator subclass.
# ---------------------------------------------------------------------------

class ValidationSimulator(BarByBarSimulator):
    """BarByBarSimulator restricted to the validation window."""
    TEST_START = VAL_START
    TEST_END   = VAL_END


# ---------------------------------------------------------------------------
# 3.  Bootstrap CI on Return(%).
# ---------------------------------------------------------------------------

def bootstrap_ci_return(equity: List[EquityPoint], n: int = N_BOOTSTRAP,
                         ci: float = 0.95) -> Tuple[float, float]:
    """
    Resample the sequence of daily PnL% contributions with replacement, n times.
    Returns (lower, upper) bound of the ci-level CI.
    """
    if len(equity) < 2:
        return (0.0, 0.0)
    vals = np.array([pt.v for pt in equity], dtype=float)
    if vals[0] != INITIAL_CAPITAL:  # first-day costs belong to the return
        vals = np.insert(vals, 0, INITIAL_CAPITAL)
    daily_ret = np.diff(vals) / vals[:-1]   # fractional daily returns

    rng = np.random.default_rng(42)
    boot_returns = []
    for _ in range(n):
        sample = rng.choice(daily_ret, size=len(daily_ret), replace=True)
        total = float(np.prod(1.0 + sample) - 1.0) * 100.0
        boot_returns.append(total)

    boot_returns.sort()
    alpha = (1.0 - ci) / 2.0
    lo = boot_returns[int(alpha * n)]
    hi = boot_returns[int((1.0 - alpha) * n)]
    return round(lo, 2), round(hi, 2)


# ---------------------------------------------------------------------------
# 4.  Random-timing baseline (same engine as ValidationSimulator, no brain logic).
# ---------------------------------------------------------------------------

def run_random_baseline(sim: ValidationSimulator, target: str,
                        n_seeds: int = N_RANDOM,
                        p_long: Optional[float] = None) -> dict:
    """
    p_long=None: uniform BUY/SELL/HOLD per day. Otherwise long with probability
    p_long each day (matches a mode's expected exposure). 200 seeds.
    Returns mean and std of pnl_pct across seeds.
    """
    target = target.upper()
    all_days = sim.evaluation_days
    fills, closes = price_arrays(sim, target, all_days)
    pool = [Action.BUY, Action.SELL, Action.HOLD]

    pnl_list: List[float] = []
    for seed in range(n_seeds):
        rng = random.Random(seed + 11000)
        if p_long is None:
            positions = [1 if rng.choice(pool) == Action.BUY else 0 for _ in all_days]
        else:
            positions = [1 if rng.random() < p_long else 0 for _ in all_days]
        pnl_list.append(simulate_positions(target, all_days, positions, fills, closes).pnl_pct)

    arr = np.array(pnl_list)
    return {
        "mean_pnl_pct": round(float(arr.mean()), 2),
        "std_pnl_pct":  round(float(arr.std()),  2),
        "min_pnl_pct":  round(float(arr.min()),  2),
        "max_pnl_pct":  round(float(arr.max()),  2),
    }


def buy_and_hold_risk(sim: ValidationSimulator, target: str) -> Tuple[float, float]:
    """(MaxDD%, Sharpe) of the buy-and-hold equity curve, same fills as the
    benchmark return and the same metric code as the strategies."""
    equity = sim.buy_and_hold_curve(target)
    n = len(equity)
    perf = compute_full_metrics([], equity, n, n, 0.0, INITIAL_CAPITAL)
    return perf.max_drawdown_pct, perf.sharpe_ratio


# ---------------------------------------------------------------------------
# 5.  Debate-change analysis.
# ---------------------------------------------------------------------------

def debate_change_analysis(
    sw_result: SimulationResult,
    db_result: SimulationResult,
    spy_df: pd.DataFrame,
    btc_df,
    target: str,
) -> dict:
    """
    Compare daily final_action between SILENT_WEIGHTED (sw) and DEBATE (db).
    For each day where they differ, check whether the debate action was better:
      better = action sign matches sign of realised next-day return.
    'BUY' is correct if next close > this close (positive return).
    'SELL' correct if negative.  'HOLD' excluded from scoring.
    Returns a summary dict.
    """
    target = target.upper()
    spy_by_date = {row["parsed_date"]: row for _, row in spy_df.iterrows()}

    sw_map = {d.date: d.final_action for d in sw_result.daily_decisions}
    db_map = {d.date: d.final_action for d in db_result.daily_decisions}

    all_dates = sorted(set(sw_map) & set(db_map))
    n_changed = 0
    n_better  = 0
    n_worse   = 0
    n_neutral = 0   # one of the actions is HOLD so cannot score

    for i, d_str in enumerate(all_dates):
        sw_a = sw_map[d_str]
        db_a = db_map[d_str]
        if sw_a == db_a:
            continue
        n_changed += 1

        # Next-day realised return
        if i + 1 >= len(all_dates):
            n_neutral += 1
            continue
        next_d = all_dates[i + 1]

        if target == "US":
            curr_cl = float(spy_by_date[pd.to_datetime(d_str).date()]["Close"]) \
                      if pd.to_datetime(d_str).date() in spy_by_date else None
            next_cl = float(spy_by_date[pd.to_datetime(next_d).date()]["Close"]) \
                      if pd.to_datetime(next_d).date() in spy_by_date else None
        else:
            def _btc_close(ds):
                cutoff = get_us_close_utc(ds)
                sub = btc_df[btc_df["close_dt"] <= cutoff]
                return float(sub.iloc[-1]["Close"]) if len(sub) else None
            curr_cl = _btc_close(d_str)
            next_cl = _btc_close(next_d)

        if curr_cl is None or next_cl is None or curr_cl == 0:
            n_neutral += 1
            continue

        ret_sign = 1 if next_cl > curr_cl else (-1 if next_cl < curr_cl else 0)

        def _action_sign(a: Action) -> int:
            return 1 if a == Action.BUY else (-1 if a == Action.SELL else 0)

        db_sign = _action_sign(db_a)
        if db_sign == 0:
            n_neutral += 1
            continue

        if db_sign == ret_sign:
            n_better += 1
        elif ret_sign == 0:
            n_neutral += 1
        else:
            n_worse += 1

    return {
        "total_days": len(all_dates),
        "n_changed": n_changed,
        "n_better": n_better,
        "n_worse": n_worse,
        "n_neutral": n_neutral,
        "pct_changed": round(n_changed / len(all_dates) * 100, 1) if all_dates else 0,
    }


def run_debate_counted(sim: ValidationSimulator, target: str,
                       brain: Optional[RuleBrain] = None) -> Tuple[SimulationResult, Counter]:
    """DEBATE run plus counts of what happened on the board."""
    counts: Counter = Counter()
    original = replay.run_mode

    def spy(**kw):
        out = original(**kw)
        msgs = kw["board"].get_all(kw["session_id"])
        position = {m.from_market: m.position for m in msgs if m.msg_type == MsgType.RECOMMEND}
        replies = [m for m in msgs if m.msg_type == MsgType.REPLY]
        counts["challenge_days"] += any(m.msg_type == MsgType.CHALLENGE for m in msgs)
        counts["replies"] += len(replies)
        for m in replies:
            counts["reply_changes"] += m.position != position[m.from_market]
            position[m.from_market] = m.position
        counts["final_stance_changes"] += sum(
            m.position != position[m.from_market] for m in msgs if m.msg_type == MsgType.FINAL
        )
        return out

    replay.run_mode = spy
    try:
        result = sim.run_simulation(target_market=target, mode=Mode.DEBATE,
                                    allow_short=False, brain=brain)
    finally:
        replay.run_mode = original
    return result, counts


# ---------------------------------------------------------------------------
# 6.  Main experiment loop.
# ---------------------------------------------------------------------------

@dataclass
class RunSummary:
    target: str
    mode: str
    pnl_pct: float
    max_dd: float
    sharpe: float
    hit_rate: float
    exposure: float
    trades: int
    turnover: float
    vetoes: int
    bh_pct: float
    bh_x_expo: float
    ci_lo: float
    ci_hi: float
    run_id: str = ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default=None,
                        help="SQLite DB path to persist runs (optional).")
    args = parser.parse_args()

    spy_path = DATA_CACHE_DIR / "spy_daily.csv"
    btc_path = DATA_CACHE_DIR / "btc_1h.csv"
    tmp_knowledge = Path(__file__).resolve().parent.parent / "knowledge_val"

    # 1. Build 2022-2023 knowledge
    print("Step 1: Building validation knowledge (2022-2023 only)…")
    build_validation_knowledge(tmp_knowledge)

    # 2. Instantiate validation simulator (overrides knowledge dir via monkey-patch)
    print("Step 2: Instantiating ValidationSimulator…")
    sim = ValidationSimulator(
        initial_capital=INITIAL_CAPITAL,
        spy_path=spy_path,
        btc_path=btc_path,
    )
    print(f"  Evaluation days: {len(sim.evaluation_days)}, "
          f"Degraded: {len(sim.degraded_days)}")

    # Patch knowledge loader so agents load from tmp_knowledge
    import app.signals.knowledge_loader as kl
    orig_knowledge_dir = kl.KNOWLEDGE_DIR
    kl.KNOWLEDGE_DIR = tmp_knowledge

    db_session = None
    if args.db_path:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.db.tables import Base
        engine = create_engine(f"sqlite:///{args.db_path}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        db_session = Session()

    summaries: List[RunSummary] = []
    all_results: Dict[str, Dict[str, SimulationResult]] = {}  # target -> mode -> result

    modes = [
        (Mode.SINGLE,            "SINGLE"),
        (Mode.SILENT_UNWEIGHTED, "SILENT_UW"),
        (Mode.SILENT_WEIGHTED,   "SILENT_W"),
        (Mode.DEBATE,            "DEBATE"),
    ]

    debate_counts: Dict[Tuple[str, str], Counter] = {}

    # 3. Run all modes × targets
    for target in ["US", "CRYPTO"]:
        all_results[target] = {}
        for mode_enum, mode_label in modes:
            print(f"  Running {target} / {mode_label}…")
            if mode_enum == Mode.DEBATE:
                result, debate_counts[(target, "learned")] = run_debate_counted(sim, target)
            else:
                result = sim.run_simulation(
                    target_market=target,
                    mode=mode_enum,
                    allow_short=False,
                )
            all_results[target][mode_label] = result
            ci_lo, ci_hi = bootstrap_ci_return(result.equity_curve)

            run_id = ""
            if db_session:
                from app.services.run_persistence import persist_run
                run_id = persist_run(
                    db_session, result,
                    run_name=f"val-{target.lower()}-{mode_label.lower()}",
                    notes="validation experiment 2024, knowledge 2022-2023",
                )

            summaries.append(RunSummary(
                target=target,
                mode=mode_label,
                pnl_pct=result.pnl_pct,
                max_dd=result.max_drawdown_pct,
                sharpe=result.sharpe_ratio,
                hit_rate=result.hit_rate_pct,
                exposure=result.exposure_pct,
                trades=result.trade_count,
                turnover=result.turnover,
                vetoes=result.risk_veto_count,
                bh_pct=result.benchmark_buy_hold_return_pct,
                bh_x_expo=result.buy_hold_exposure_scaled_return_pct,
                ci_lo=ci_lo,
                ci_hi=ci_hi,
                run_id=run_id,
            ))

    # 4. Ablation: DEBATE with the original thresholds (needs validation knowledge)
    for target in ["US", "CRYPTO"]:
        all_results[target]["DEBATE_ORIG"], debate_counts[(target, "original")] = (
            run_debate_counted(sim, target, brain=RuleBrain(thresholds={}))
        )

    # Debate-change analysis vs SILENT_WEIGHTED
    kl.KNOWLEDGE_DIR = orig_knowledge_dir  # restore
    print("Step 3: Debate-change analysis…")
    btc_df_full = sim.btc_df
    btc_df_full["close_dt"] = btc_df_full["open_dt"] + pd.Timedelta(hours=1)

    change_results: Dict[Tuple[str, str], dict] = {}
    for target in ["US", "CRYPTO"]:
        sw = all_results[target]["SILENT_W"]
        for label, key in (("learned", "DEBATE"), ("original", "DEBATE_ORIG")):
            db = all_results[target][key]
            row = debate_change_analysis(sw, db, sim.spy_df, btc_df_full, target)
            row.update(debate_counts[(target, label)])
            row["return_pct"], row["max_dd"] = db.pnl_pct, db.max_drawdown_pct
            change_results[(target, label)] = row

    # 5. Random baselines
    print("Step 4: Random-timing baselines (200 seeds)…")
    random_baselines: Dict[str, dict] = {}
    for target in ["US", "CRYPTO"]:
        random_baselines[target] = run_random_baseline(sim, target)
    matched: Dict[Tuple[str, str], dict] = {
        (s.target, s.mode): run_random_baseline(sim, s.target, p_long=s.exposure / 100.0)
        for s in summaries
    }

    # 6. Write report
    _write_report(summaries, change_results, random_baselines, matched, sim, db_session)

    if db_session:
        db_session.close()

    print("Done.")


# ---------------------------------------------------------------------------
# 7.  Report
# ---------------------------------------------------------------------------

def _write_report(
    summaries: List[RunSummary],
    change_results: dict,
    random_baselines: dict,
    matched: dict,
    sim: ValidationSimulator,
    db_session,
) -> None:
    out = Path(__file__).resolve().parent.parent.parent / "docs" / "status" / "validation_experiment.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    bh_us     = sim.compute_buy_and_hold("US")
    bh_crypto = sim.compute_buy_and_hold("CRYPTO")

    lines = [
        "# Mode Comparison — Validation Window (2024-01-01 to 2024-12-31)",
        "",
        "> **Preliminary (FYP1).** Knowledge learned on 2022-01-03 to 2023-12-31 only.",
        "> Test window (2025-01-01 to 2026-11-20) is held out.",
        "> Drawdown cool-off lengths were selected on this window; debate thresholds come from the learning window.",
        "",
        f"**Evaluation days:** {len(sim.evaluation_days)}  |  "
        f"**Degraded days (excluded):** {len(sim.degraded_days)}",
        "",
        "## 1. Mode Comparison",
        "",
        "| Target | Mode | Return(%) | 95% CI | MaxDD(%) | Sharpe | HitRate(%) |"
        " Exposure(%) | Trades | Turnover | Vetoes | RunID |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in summaries:
        lines.append(
            f"| {s.target} | {s.mode} | {s.pnl_pct:+.2f} |"
            f" [{s.ci_lo:+.2f}, {s.ci_hi:+.2f}] |"
            f" {s.max_dd:.2f} | {s.sharpe:.2f} | {s.hit_rate:.1f} |"
            f" {s.exposure:.1f} | {s.trades} | {s.turnover:.2f}x | {s.vetoes} |"
            f" {s.run_id or '—'} |"
        )

    lines += [
        "",
        "## 2. Benchmarks",
        "",
        "| Target | Benchmark | Return(%) | MaxDD(%) | Sharpe | Entry Price | Exit Price |",
        "|---|---|---|---|---|---|---|",
    ]
    for target, bh in (("US", bh_us), ("CRYPTO", bh_crypto)):
        dd, sharpe = buy_and_hold_risk(sim, target)
        lines.append(
            f"| {target} | Buy-and-Hold | {bh.return_pct:+.2f} | {dd:.2f} | {sharpe:.2f} |"
            f" {bh.entry_fill_price:.2f} | {bh.exit_fill_price:.2f} |"
        )
        lines.append(f"| {target} | Always-Flat | +0.00 | 0.00 | 0.00 | — | — |")
    for target, rb in random_baselines.items():
        lines.append(
            f"| {target} | Random uniform (mean±std, {N_RANDOM} seeds) |"
            f" {rb['mean_pnl_pct']:+.2f}±{rb['std_pnl_pct']:.2f}"
            f" [{rb['min_pnl_pct']:+.2f}, {rb['max_pnl_pct']:+.2f}] | — | — | — | — |"
        )
    lines += [
        "",
        "### Per mode: same exposure",
        "",
        f"Random = long each day with probability equal to the mode's exposure, {N_RANDOM} seeds.",
        "",
        "| Target | Mode | Exposure(%) | Mode return(%) | B&H×Exposure(%) |"
        " Matched random mean±std [min, max] |",
        "|---|---|---|---|---|---|",
    ]
    for s in summaries:
        rb = matched[(s.target, s.mode)]
        lines.append(
            f"| {s.target} | {s.mode} | {s.exposure:.1f} | {s.pnl_pct:+.2f} | {s.bh_x_expo:+.2f} |"
            f" {rb['mean_pnl_pct']:+.2f}±{rb['std_pnl_pct']:.2f}"
            f" [{rb['min_pnl_pct']:+.2f}, {rb['max_pnl_pct']:+.2f}] |"
        )

    lines += [
        "",
        "## 3. Debate vs Silent-Weighted — Change Analysis",
        "",
        "'learned' = each agent's learning-window 90th percentile "
        f"({json.dumps(json.loads(THRESHOLDS_FILE.read_text())['thresholds'])}); "
        "'original' = 2.0 / 2.4 / 2.0 (ablation). The change was decided after seeing the"
        " earlier validation result (protocol.md section 12).",
        "",
        "Final changes = days the post-risk final action differs from SILENT_W. Better/Worse"
        " score the debate action against the next-day return; a change to HOLD cannot be"
        " scored and counts as Neutral.",
        "",
        "| Target | Thresholds | Challenge days | Replies | Stance changes (reply / final round) |"
        " Final changes vs SILENT_W | Better | Worse | Neutral | Return(%) | MaxDD(%) |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for (target, label), cr in change_results.items():
        lines.append(
            f"| {target} | {label} | {cr['challenge_days']} | {cr['replies']} |"
            f" {cr['reply_changes']} / {cr['final_stance_changes']} |"
            f" {cr['n_changed']} of {cr['total_days']} | {cr['n_better']} | {cr['n_worse']} |"
            f" {cr['n_neutral']} | {cr['return_pct']:+.2f} | {cr['max_dd']:.2f} |"
        )

    lines += [
        "",
        "## 4. Notes",
        "",
        "- Return(%) is measured from initial capital. MaxDD and Sharpe follow the daily curve.",
        "- Bootstrap CIs resample daily PnL% contributions (2000 iterations, seed=42).",
        "- Random-timing baselines are long/flat and run on the shared engine. Matched random"
        " draws each day independently, so it trades more than the modes and pays more friction.",
        "- Buy-and-Hold pays the same slippage and commission as the strategies.",
        "- All fills use the same rules as BarByBarSimulator (SPY: next-open;"
        " BTC: first 1h candle at 21:00 UTC cutoff).",
        "- Veto counts are days overridden by volatility, drawdown breach or cool-off.",
        "",
        "## 5. Known Limitations (read before citing)",
        "",
        "- All 2024 figures are optimistic: cool-off lengths (US 5, CRYPTO 20) were selected on this"
        " window, and the debate thresholds were changed after seeing its result.",
        "- The cool-off grid was repeated with the final code; the chosen values did not change."
        "",
        "- The drawdown peak is rebased at each re-arm, so total drawdown can exceed the 5% limit.",
        "- HOLD keeps the open position (protocol.md section 10); chosen to match the protocol,"
        " not for returns.",
        "- In the uniform and matched random baselines a non-BUY day is flat, not 'keep'.",
        "- CRYPTO agents use hourly candles and US agents daily candles.",
        "- One year, two assets; the bootstrap intervals are wide. No mode is shown to be better.",
        "",
        "## 6. Future Work",
        "",
        "- Debate can only move a stance to HOLD; it cannot turn BUY into SELL or open a trade.",
        "- A reply ignores the challenge's content and evidence: only the replier's own volatility"
        " decides. Replies should weigh what the challenger argues.",
    ]

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report written to {out}")


if __name__ == "__main__":
    main()
