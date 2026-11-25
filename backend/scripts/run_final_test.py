"""
The one counted run on the held-out test window (protocol.md sections 2, 3, 13).

    python scripts/run_final_test.py --final-test

Refuses to run without --final-test, if the lock file exists, or if any frozen
file differs from the hash table in protocol.md. The lock is written BEFORE the
run, so a crashed run also locks; what to do then is a human decision, recorded
as an erratum.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

BACKEND = Path(__file__).resolve().parent.parent
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

TEST_START, TEST_END = "2025-01-01", "2026-11-20"
LOCK_PATH = ROOT / "docs" / "status" / "FINAL_TEST.lock"
OUT_PATH = ROOT / "docs" / "status" / "test_results.md"
PROTOCOL_PATH = ROOT / "docs" / "status" / "protocol.md"
THRESHOLDS_PATH = BACKEND / "app" / "config" / "debate_thresholds_test.json"


def frozen_files() -> List[str]:
    """Repo-relative paths of everything that determines the test numbers."""
    paths = [p for p in (BACKEND / "app").rglob("*") if p.suffix in (".py", ".yaml", ".json")]
    paths += [BACKEND / "knowledge" / n for n in ("us.json", "crypto.json")]
    paths += [BACKEND / "data_cache" / n for n in ("spy_daily.csv", "btc_1h.csv")]
    paths += [BACKEND / "scripts" / n for n in (
        "run_final_test.py", "run_validation_experiment.py", "run_rule_baselines.py")]
    return sorted(p.relative_to(ROOT).as_posix() for p in paths if "__pycache__" not in p.parts)


def file_hash(relative: str) -> str:
    """SHA-256 with CRLF normalised, so a checkout setting cannot change it."""
    return hashlib.sha256((ROOT / relative).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def hash_table() -> str:
    return "\n".join(["| File | SHA-256 |", "|---|---|"]
                     + [f"| `{f}` | `{file_hash(f)}` |" for f in frozen_files()])


def frozen_mismatches(protocol_text: str) -> List[str]:
    return [f for f in frozen_files() if f"| `{f}` | `{file_hash(f)}` |" not in protocol_text]


def acquire_lock(path: Path) -> None:
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        with open(path, "x", encoding="utf-8") as fh:
            fh.write(f"final test started {stamp}\n")
    except FileExistsError:
        raise SystemExit(f"Refusing to run: lock file exists ({path}): {path.read_text().strip()}")


def run_experiment(start: str, end: str, knowledge_dir: Path, thresholds_path: Path,
                   out_path: Path) -> None:
    """All modes and baselines on [start, end]. Parametrised so it can be
    rehearsed on the validation window."""
    import app.signals.knowledge_loader as kl
    import run_rule_baselines as rules
    import run_validation_experiment as ve
    from app.agents.brains.rule_brain import RuleBrain
    from app.config.settings import DATA_CACHE_DIR, DRAWDOWN_COOLOFF_DAYS_BY_TARGET
    from app.domain.enums import Mode

    window = type("_Window", (ve.ValidationSimulator,), {"TEST_START": start, "TEST_END": end})
    thresholds = json.loads(thresholds_path.read_text(encoding="utf-8"))["thresholds"]
    original_dir = kl.KNOWLEDGE_DIR
    kl.KNOWLEDGE_DIR = knowledge_dir
    try:
        sim = window()
        brain = RuleBrain(thresholds=thresholds)
        modes = [("SINGLE", Mode.SINGLE), ("SILENT_UW", Mode.SILENT_UNWEIGHTED),
                 ("SILENT_W", Mode.SILENT_WEIGHTED), ("DEBATE", Mode.DEBATE)]
        mode_rows, bench_rows, debate_rows = [], [], []
        for target in ["US", "CRYPTO"]:
            results = {}
            for label, mode in modes:
                if mode == Mode.DEBATE:
                    result, counts = ve.run_debate_counted(sim, target, brain=brain)
                else:
                    result = sim.run_simulation(target, mode, brain=brain)
                results[label] = result
                lo, hi = ve.bootstrap_ci_return(result.equity_curve)
                rnd = ve.run_random_baseline(sim, target, p_long=result.exposure_pct / 100.0)
                mode_rows.append(
                    f"| {target} | {label} | {result.pnl_pct:+.2f} | [{lo:+.2f}, {hi:+.2f}] |"
                    f" {result.max_drawdown_pct:.2f} | {result.sharpe_ratio:.2f} |"
                    f" {result.hit_rate_pct:.1f} | {result.exposure_pct:.1f} | {result.trade_count} |"
                    f" {result.turnover:.2f}x | {result.risk_veto_count} |"
                    f" {result.buy_hold_exposure_scaled_return_pct:+.2f} |"
                    f" {rnd['mean_pnl_pct']:+.2f}±{rnd['std_pnl_pct']:.2f} |")
            bh = sim.compute_buy_and_hold(target)
            dd, sharpe = ve.buy_and_hold_risk(sim, target)
            uniform = ve.run_random_baseline(sim, target)
            bench_rows += [
                f"| {target} | Buy-and-Hold | {bh.return_pct:+.2f} | {dd:.2f} | {sharpe:.2f} |",
                f"| {target} | Always-Flat | +0.00 | 0.00 | 0.00 |",
                f"| {target} | Random uniform (200 seeds) |"
                f" {uniform['mean_pnl_pct']:+.2f}±{uniform['std_pnl_pct']:.2f} | — | — |",
            ]
            change = ve.debate_change_analysis(
                results["SILENT_W"], results["DEBATE"], sim.spy_df, sim.btc_df, target)
            debate_rows.append(
                f"| {target} | {counts['challenge_days']} | {counts['replies']} |"
                f" {counts['reply_changes']} / {counts['final_stance_changes']} |"
                f" {change['n_changed']} of {change['total_days']} | {change['n_better']} |"
                f" {change['n_worse']} | {change['n_neutral']} |")
        rule_results = rules._run_all(
            DATA_CACHE_DIR / "spy_daily.csv", DATA_CACHE_DIR / "btc_1h.csv", start, end)
    finally:
        kl.KNOWLEDGE_DIR = original_dir

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                            text=True).stdout.strip()
    lines = [
        f"# Results — window {start} to {end}",
        "",
        f"Run at {datetime.now(timezone.utc).isoformat(timespec='seconds')}, commit `{commit}`.",
        f"Evaluation days: {len(sim.evaluation_days)}; degraded (excluded): {len(sim.degraded_days)}.",
        f"Debate thresholds: {thresholds}. Cool-off days: {DRAWDOWN_COOLOFF_DAYS_BY_TARGET}.",
        "Bugs found after this run are recorded as errata, not silently rerun.",
        "",
        "## 1. Modes",
        "",
        "| Target | Mode | Return(%) | 95% CI | MaxDD(%) | Sharpe | HitRate(%) | Exposure(%) |"
        " Trades | Turnover | Vetoes | B&H×Exposure(%) | Matched random(%) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        *mode_rows,
        "",
        "## 2. Benchmarks",
        "",
        "| Target | Benchmark | Return(%) | MaxDD(%) | Sharpe |",
        "|---|---|---|---|---|",
        *bench_rows,
        "",
        "## 3. Debate vs Silent-Weighted",
        "",
        "| Target | Challenge days | Replies | Stance changes (reply / final) | Final changes |"
        " Better | Worse | Neutral |",
        "|---|---|---|---|---|---|---|---|",
        *debate_rows,
        "",
        "## 4. Rule baselines R1-R5",
        "",
        *rules.NOTES,
        "",
        *rules.result_table(rule_results),
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report written to {out_path}")


def main(argv: Optional[List[str]] = None, lock_path: Path = LOCK_PATH) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final-test", action="store_true",
                        help="required: run the held-out test window, once")
    args = parser.parse_args(argv)
    if not args.final_test:
        raise SystemExit("Refusing to run: pass --final-test to open the held-out test window.")
    if lock_path.exists():
        raise SystemExit(f"Refusing to run: lock file exists ({lock_path}).")
    changed = frozen_mismatches(PROTOCOL_PATH.read_text(encoding="utf-8"))
    if changed:
        raise SystemExit("Refusing to run: files differ from protocol.md freeze table:\n  "
                         + "\n  ".join(changed))
    acquire_lock(lock_path)
    run_experiment(TEST_START, TEST_END, BACKEND / "knowledge", THRESHOLDS_PATH, OUT_PATH)


if __name__ == "__main__":
    main()
