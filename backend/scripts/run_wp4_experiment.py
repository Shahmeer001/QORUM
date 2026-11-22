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

    print("\n" + "=" * 80)
    print("WP4 EXPERIMENT RESULTS TABLE (REPORTED SEPARATELY)")
    print("=" * 80)
    print(f"{'Target Market':<10} | {'Shorting':<10} | {'Start Eq':<10} | {'End Eq':<10} | {'Net PnL ($)':<12} | {'Return (%)':<10} | {'Max DD (%)':<10} | {'Hit Rate':<10} | {'Exposure':<10} | {'Trades':<8} | {'Turnover':<8}")
    print("-" * 115)

    runs = [
        ("US (SPY)", "Long/Flat", res_us_long),
        ("US (SPY)", "Long/Short", res_us_short),
        ("CRYPTO (BTC)", "Long/Flat", res_crypto_long),
        ("CRYPTO (BTC)", "Long/Short", res_crypto_short),
    ]

    for label, short_lbl, r in runs:
        print(
            f"{label:<10} | {short_lbl:<10} | ${r.initial_capital:<9.2f} | ${r.final_equity:<9.2f} | "
            f"${r.pnl_dollars:<11.2f} | {r.pnl_pct:>9.2f}% | {r.max_drawdown_pct:>9.2f}% | "
            f"{r.hit_rate_pct:>8.1f}% | {r.exposure_pct:>8.1f}% | {r.trade_count:>6} | {r.turnover:>7.2f}x"
        )
    print("=" * 115)

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
