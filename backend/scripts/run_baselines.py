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
import pandas as pd

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.settings import INITIAL_CAPITAL, get_us_close_utc
from app.domain.enums import Action
from app.domain.models import EquityPoint, Trade
from app.simulator.metrics import compute_full_metrics
from app.simulator.replay_simulator import BarByBarSimulator
from app.simulator.trade_engine import (
    calculate_trade_pnl,
    execute_fill,
    get_market_friction,
)


def run_buy_and_hold(sim: BarByBarSimulator, target_market: str) -> dict:
    target = target_market.upper()
    friction = get_market_friction(target)
    all_eval_days = sim.evaluation_days
    n_days = len(all_eval_days)

    if target == "US":
        spy_by_date = {row["parsed_date"]: row for _, row in sim.spy_df.iterrows()}
        # Enters at day 1 Open (fill from day 0 decision)
        first_open = float(spy_by_date[all_eval_days[1]]["Open"])
        last_close = float(spy_by_date[all_eval_days[-1]]["Close"])
        entry_raw = first_open
        exit_raw = last_close
    else:  # CRYPTO
        c0 = get_us_close_utc(all_eval_days[0].isoformat())
        c_last = get_us_close_utc(all_eval_days[-1].isoformat())
        entry_raw = float(sim.btc_df[sim.btc_df["open_dt"] >= c0].iloc[0]["Open"])
        exit_raw = float(sim.btc_df[sim.btc_df["close_dt"] <= c_last].iloc[-1]["Close"])

    entry_fill = execute_fill(Action.BUY, entry_raw, friction, is_entry=True)
    exit_fill = execute_fill(Action.BUY, exit_raw, friction, is_entry=False)
    units = INITIAL_CAPITAL / entry_fill
    net_pnl, total_comm, gross = calculate_trade_pnl(entry_fill, exit_fill, units, friction)

    trade = Trade(
        entry=f"{all_eval_days[0].isoformat()} Entry",
        exit=f"{all_eval_days[-1].isoformat()} Exit",
        side=Action.BUY,
        market=target,
        pnl=round(net_pnl, 2),
        note="Buy and Hold Benchmark",
    )

    # Build mark to market equity
    equity = []
    cash = INITIAL_CAPITAL - (units * entry_fill) - (units * entry_fill * friction.commission)
    for eval_d in all_eval_days:
        if target == "US":
            row = spy_by_date.get(eval_d)
            c_price = float(row["Close"]) if row is not None else exit_raw
        else:
            cutoff = get_us_close_utc(eval_d.isoformat())
            c_price = float(sim.btc_df[sim.btc_df["close_dt"] <= cutoff].iloc[-1]["Close"])
        eq = cash + units * c_price
        equity.append(EquityPoint(t=eval_d.isoformat(), v=round(eq, 2)))

    perf = compute_full_metrics(
        trades=[trade],
        equity=equity,
        total_days=n_days,
        days_exposed=n_days,
        total_volume_traded=units * entry_fill + units * exit_fill,
        initial_capital=INITIAL_CAPITAL,
    )
    return {
        "strategy": "Buy & Hold",
        "target": target,
        "final_equity": perf.end_equity,
        "pnl_dollars": perf.pnl_dollars,
        "return_pct": perf.pnl_pct,
        "max_dd_pct": perf.max_drawdown_pct,
        "sharpe": perf.sharpe_ratio,
        "exposure_pct": perf.exposure_pct,
        "trade_count": perf.trade_count,
        "turnover": perf.turnover,
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
    friction = get_market_friction(target)
    all_eval_days = sim.evaluation_days
    n_days = len(all_eval_days)
    spy_by_date = {row["parsed_date"]: row for _, row in sim.spy_df.iterrows()} if target == "US" else {}

    returns = []
    drawdowns = []
    sharpes = []
    trades_counts = []
    turnovers = []

    actions_pool = [Action.BUY, Action.SELL, Action.HOLD]

    for seed in range(n_seeds):
        rng = random.Random(seed + 1000)
        cash = INITIAL_CAPITAL
        pos = 0  # 0 or 1
        units = 0.0
        entry_fill = 0.0
        tot_vol = 0.0
        trades = []
        equity = []
        days_exp = 0

        for i, eval_d in enumerate(all_eval_days):
            d_str = eval_d.isoformat()
            act = rng.choice(actions_pool)
            target_pos = 1 if act == Action.BUY else 0

            # Price
            if target == "US":
                if i + 1 < n_days:
                    exec_raw = float(spy_by_date[all_eval_days[i + 1]]["Open"])
                    curr_close = float(spy_by_date[eval_d]["Close"])
                else:
                    exec_raw = float(spy_by_date[eval_d]["Close"])
                    curr_close = exec_raw
            else:
                cutoff = get_us_close_utc(d_str)
                next_candle = sim.btc_df[sim.btc_df["open_dt"] >= cutoff].head(1)
                exec_raw = float(next_candle.iloc[0]["Open"]) if len(next_candle) > 0 else 50000.0
                curr_close = float(sim.btc_df[sim.btc_df["close_dt"] <= cutoff].iloc[-1]["Close"])

            if target_pos != pos:
                if pos == 1:
                    exit_fill_price = execute_fill(Action.SELL, exec_raw, friction, is_entry=False)
                    pnl, comm, _ = calculate_trade_pnl(entry_fill, exit_fill_price, units, friction)
                    exit_notional = units * exit_fill_price
                    cash += exit_notional - (exit_notional * friction.commission)
                    tot_vol += exit_notional
                    trades.append(Trade(entry="e", exit="x", side=Action.BUY, market=target, pnl=round(pnl, 2), note=""))
                    pos = 0
                    units = 0.0
                if target_pos == 1:
                    entry_fill_price = execute_fill(Action.BUY, exec_raw, friction, is_entry=True)
                    units = cash / entry_fill_price if entry_fill_price > 0 else 0.0
                    entry_notional = units * entry_fill_price
                    cash -= entry_notional + (entry_notional * friction.commission)
                    tot_vol += entry_notional
                    entry_fill = entry_fill_price
                    pos = 1

            if pos == 1:
                eq = cash + units * curr_close
                days_exp += 1
            else:
                eq = cash
            equity.append(EquityPoint(t=d_str, v=round(eq, 2)))

        if pos == 1:
            exit_fill_price = execute_fill(Action.SELL, curr_close, friction, is_entry=False)
            pnl, comm, _ = calculate_trade_pnl(entry_fill, exit_fill_price, units, friction)
            exit_notional = units * exit_fill_price
            cash += exit_notional - (exit_notional * friction.commission)
            tot_vol += exit_notional
            trades.append(Trade(entry="e", exit="x", side=Action.BUY, market=target, pnl=round(pnl, 2), note=""))
            equity[-1] = EquityPoint(t=all_eval_days[-1].isoformat(), v=round(cash, 2))

        perf = compute_full_metrics(trades, equity, n_days, days_exp, tot_vol, INITIAL_CAPITAL)
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
