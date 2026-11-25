"""
WP4 Baseline Comparisons & Random Trader Benchmark.
Runs through the EXACT same engine, fills, friction, test window (2025-01-01 to 2026-11-20),
and evaluation days (474 days):
1. Buy-and-Hold for US (SPY) and CRYPTO (BTC)
2. Always-Flat (Zero exposure)
3. Seeded Random Trader: 200 random seeds (evaluates mean and spread of return, drawdown, Sharpe)
"""
from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Dict, List

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.settings import INITIAL_CAPITAL
from app.domain.enums import Action
from app.domain.models import EquityPoint
from app.simulator.metrics import compute_full_metrics
from app.simulator.replay_simulator import BarByBarSimulator
from app.simulator.signal_engine import price_arrays, simulate_positions


def run_buy_and_hold(sim: BarByBarSimulator, target_market: str) -> dict:
    target = target_market.upper()
    equity = sim.buy_and_hold_curve(target)
    n_days = len(equity)
    perf = compute_full_metrics([], equity, n_days, n_days, 0.0, INITIAL_CAPITAL)
    return {
        "strategy": "Buy & Hold",
        "target": target,
        "final_equity": perf.end_equity,
        "pnl_dollars": perf.pnl_dollars,
        "return_pct": perf.pnl_pct,
        "max_dd_pct": perf.max_drawdown_pct,
        "sharpe": perf.sharpe_ratio,
        "exposure_pct": perf.exposure_pct,
        "trade_count": 1,
        "turnover": 0.0,
    }


def run_always_flat(sim: BarByBarSimulator, target_market: str) -> dict:
    all_eval_days = sim.evaluation_days
    n_days = len(all_eval_days)
    equity = [EquityPoint(t=d.isoformat(), v=INITIAL_CAPITAL) for d in all_eval_days]
    perf = compute_full_metrics(
        trades=[],
        equity=equity,
        total_days=n_days,
        days_exposed=0,
        total_volume_traded=0.0,
        initial_capital=INITIAL_CAPITAL,
    )
    return {
        "strategy": "Always-Flat",
        "target": target_market.upper(),
        "final_equity": perf.end_equity,
        "pnl_dollars": perf.pnl_dollars,
        "return_pct": perf.pnl_pct,
        "max_dd_pct": perf.max_drawdown_pct,
        "sharpe": perf.sharpe_ratio,
        "exposure_pct": perf.exposure_pct,
        "trade_count": perf.trade_count,
        "turnover": perf.turnover,
    }


def run_random_trader(sim: BarByBarSimulator, target_market: str, n_seeds: int = 200) -> dict:
    target = target_market.upper()
    all_eval_days = sim.evaluation_days
    fills, closes = price_arrays(sim, target, all_eval_days)

    returns = []
    drawdowns = []
    sharpes = []
    trades_counts = []
    turnovers = []

    actions_pool = [Action.BUY, Action.SELL, Action.HOLD]

    for seed in range(n_seeds):
        rng = random.Random(seed + 1000)
        positions = [1 if rng.choice(actions_pool) == Action.BUY else 0 for _ in all_eval_days]
        perf = simulate_positions(target, all_eval_days, positions, fills, closes)
        returns.append(perf.pnl_pct)
        drawdowns.append(perf.max_drawdown_pct)
        sharpes.append(perf.sharpe_ratio)
        trades_counts.append(perf.trade_count)
        turnovers.append(perf.turnover)

    mean_ret = sum(returns) / len(returns)
    std_ret = (sum((r - mean_ret) ** 2 for r in returns) / len(returns)) ** 0.5
    min_ret = min(returns)
    max_ret = max(returns)

    mean_dd = sum(drawdowns) / len(drawdowns)
    std_dd = (sum((d - mean_dd) ** 2 for d in drawdowns) / len(drawdowns)) ** 0.5

    mean_sharpe = sum(sharpes) / len(sharpes)

    return {
        "strategy": f"Random Trader ({n_seeds} seeds)",
        "target": target,
        "mean_return_pct": round(mean_ret, 2),
        "std_return_pct": round(std_ret, 2),
        "min_return_pct": round(min_ret, 2),
        "max_return_pct": round(max_ret, 2),
        "mean_max_dd_pct": round(mean_dd, 2),
        "std_max_dd_pct": round(std_dd, 2),
        "mean_sharpe": round(mean_sharpe, 2),
        "mean_trades": round(sum(trades_counts) / len(trades_counts), 1),
        "mean_turnover": round(sum(turnovers) / len(turnovers), 2),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="QUORUM Baselines Evaluation")
    parser.add_argument(
        "--persist-db",
        metavar="PATH",
        default=None,
        help="Optional SQLite DB path; persists each baseline result via persist_run.",
    )
    args = parser.parse_args()

    print("=" * 90)
    print("QUORUM BASELINES EVALUATION (SAME ENGINE, FILLS, FRICTION, AND DAYS)")
    print("=" * 90)
    sim = BarByBarSimulator()

    for target in ["US", "CRYPTO"]:
        print(f"\n--- Target: {target} ---")
        bh = run_buy_and_hold(sim, target)
        flat = run_always_flat(sim, target)
        rand = run_random_trader(sim, target, n_seeds=200)

        print(f"Buy & Hold: Return = {bh['return_pct']:>6.2f}%, Max DD = {bh['max_dd_pct']:>6.2f}%, Sharpe = {bh['sharpe']:>5.2f}, Trades = {bh['trade_count']}")
        print(f"Always-Flat: Return = {flat['return_pct']:>6.2f}%, Max DD = {flat['max_dd_pct']:>6.2f}%, Sharpe = {flat['sharpe']:>5.2f}, Trades = {flat['trade_count']}")
        print(f"Random (200 seeds): Mean Return = {rand['mean_return_pct']:>6.2f}% (+/- {rand['std_return_pct']:.2f}%), Spread = [{rand['min_return_pct']:.2f}%, {rand['max_return_pct']:.2f}%]")
        print(f"                   Mean Max DD = {rand['mean_max_dd_pct']:>6.2f}% (+/- {rand['std_max_dd_pct']:.2f}%), Mean Sharpe = {rand['mean_sharpe']:.2f}")

    if args.persist_db:
        # Persist via run_simulation for each target so persist_run receives a
        # proper SimulationResult.  This is intentionally not run by default;
        # pass --persist-db PATH to trigger it.
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.agents.brains.fake_brain import FakeBrain
        from app.domain.enums import Action, Mode
        from app.services.run_persistence import persist_run

        engine = create_engine(f"sqlite:///{args.persist_db}")
        DBSession = sessionmaker(bind=engine)
        db = DBSession()
        try:
            for target in ["US", "CRYPTO"]:
                result = sim.run_simulation(
                    target_market=target,
                    mode=Mode.DEBATE,
                    allow_short=False,
                    brain=FakeBrain(Action.BUY),
                )
                run_id = persist_run(db, result, run_name=f"baseline-buybrain-{target.lower()}", notes="run_baselines.py --persist-db")
                print(f"Persisted {target} run as {run_id}")
        finally:
            db.close()
            engine.dispose()


if __name__ == "__main__":
    main()
