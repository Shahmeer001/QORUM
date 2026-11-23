"""
WP4 Experiment Runner.
Executes bar-by-bar historical replay on out-of-sample test window (2025-01-01 to 2026-11-20).
Runs two sessions per day:
- Target: US (CRYPTO informs)
- Target: CRYPTO (US informs)
Reports targets separately (never averaged).
Computes equity, PnL ($ and %), max drawdown, hit rate, exposure, trade count, turnover.
Evaluates long/flat (default) and shorting sensitivity (allow_short=True).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.domain.enums import Mode
from app.simulator.replay_simulator import BarByBarSimulator


def run_experiments() -> None:
    print("=" * 80)
    print("QUORUM WP4 HISTORICAL BAR-BY-BAR REPLAY SIMULATION")
    print("Out-of-Sample Test Window: 2025-01-01 to 2026-11-20")
    print("Knowledge strictly trained on Learning Window: 2022-01-03 to 2024-12-31")
    print("=" * 80)

    sim = BarByBarSimulator()
    print(f"Total Evaluation Days (both markets active): {len(sim.evaluation_days)}")
    print(f"Total Degraded Days (US closed / holiday / weekend): {len(sim.degraded_days)}")
    print("-" * 80)

    # 1. Target = US (CRYPTO informs) - Long/Flat
    print("Running Target: US (CRYPTO informs) [Default Long/Flat]...")
    res_us_long = sim.run_simulation(target_market="US", mode=Mode.DEBATE, allow_short=False)

    # 2. Target = US (CRYPTO informs) - Allow Short
    print("Running Target: US (CRYPTO informs) [Sensitivity Allow Short]...")
    res_us_short = sim.run_simulation(target_market="US", mode=Mode.DEBATE, allow_short=True)

    # 3. Target = CRYPTO (US informs) - Long/Flat
    print("Running Target: CRYPTO (US informs) [Default Long/Flat]...")
    res_crypto_long = sim.run_simulation(target_market="CRYPTO", mode=Mode.DEBATE, allow_short=False)

    # 4. Target = CRYPTO (US informs) - Allow Short
    print("Running Target: CRYPTO (US informs) [Sensitivity Allow Short]...")
    res_crypto_short = sim.run_simulation(target_market="CRYPTO", mode=Mode.DEBATE, allow_short=True)

    print("\n" + "=" * 125)
    print("WP4 EXPERIMENT RESULTS TABLE — PRELIMINARY (FYP1)")
    print("Mode: DEBATE MODE (Two sessions/day: US informed by CRYPTO; CRYPTO informed by US)")
    print("Reported separately per target market (never averaged), evaluated on 474 evaluation days")
    print("=" * 125)
    print(
        f"{'Target Market':<10} | {'Mode':<8} | {'Stance':<10} | {'Return (%)':<10} | {'Max DD (%)':<10} | "
        f"{'Sharpe':<7} | {'B&H xExpo':<11} | {'Hit Rate':<9} | {'Exposure':<9} | {'Trades':<7} | {'Turnover':<8} | {'Days':<5}"
    )
    print("-" * 125)

    runs = [
        ("US (SPY)", "Debate", "Long/Flat", res_us_long),
        ("US (SPY)", "Debate", "Long/Short", res_us_short),
        ("CRYPTO (BTC)", "Debate", "Long/Flat", res_crypto_long),
        ("CRYPTO (BTC)", "Debate", "Long/Short", res_crypto_short),
    ]

    for label, mode_lbl, short_lbl, r in runs:
        print(
            f"{label:<10} | {mode_lbl:<8} | {short_lbl:<10} | {r.pnl_pct:>9.2f}% | {r.max_drawdown_pct:>9.2f}% | "
            f"{r.sharpe_ratio:>7.2f} | {r.buy_hold_exposure_scaled_return_pct:>10.2f}% | {r.hit_rate_pct:>8.1f}% | "
            f"{r.exposure_pct:>8.1f}% | {r.trade_count:>7} | {r.turnover:>7.2f}x | {r.evaluation_days_count:<5}"
        )
    print("=" * 125)

    # Buy-and-hold benchmark entry/exit prices and dates (Part B3).
    print("\nBuy-and-Hold Benchmark (same fill rule + same final mark as the strategy):")
    for label, _, _, r in runs:
        print(
            f"  {label:<14}: entry {r.benchmark_buy_hold_entry_price:.2f} @ {r.benchmark_buy_hold_entry_date} | "
            f"exit {r.benchmark_buy_hold_exit_price:.2f} @ {r.benchmark_buy_hold_exit_date} | "
            f"B&H return {r.benchmark_buy_hold_return_pct:.2f}% | B&H x exposure {r.buy_hold_exposure_scaled_return_pct:.2f}%"
        )

    print("\nDegraded Days Count Summary:")
    print(f"Total Degraded Days excluded from main evaluation metrics: {len(sim.degraded_days)}")
    # Sample degraded day reasons
    sample_reasons = {}
    for d in sim.degraded_days:
        reason = d["reason"]
        sample_reasons[reason] = sample_reasons.get(reason, 0) + 1
    for r, cnt in sample_reasons.items():
        print(f"  - {r}: {cnt} days")


if __name__ == "__main__":
    run_experiments()
