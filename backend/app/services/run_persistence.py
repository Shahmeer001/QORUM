"""
Persistence helpers for simulation runs (Part 0.5 / Item 5).

The replay simulator returns a SimulationResult with daily_decisions, trades,
equity_curve, and risk_events. This module persists them to SQLite so the
experiment run can be audited later via the DB.

Stored per run:
  - runs row (top-level metadata)
  - daily_decisions rows (one per day)
  - trades rows (one per Trade in result.trades)
  - equity_points rows (one per EquityPoint in result.equity_curve)
  - risk_events: not stored per-day yet — documented as follow-up.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.tables import DailyDecisionTable, EquityPointTable, TradeTable
from app.simulator.replay_simulator import DailyDecisionRecord, SimulationResult


def persist_run(
    db: Session,
    result: SimulationResult,
    run_name: str,
    notes: str = "",
) -> str:
    """
    Persist a simulation result: run metadata, daily decisions, trades, and
    equity curve.  Returns the run_id.

    Per-day risk events are not stored yet (schema has a risk_events table keyed
    to session_id, not run_id; persisting them is a documented follow-up once the
    per-run session structure is clarified).
    """
    run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{result.target_market}-{result.mode.value}"

    # 1. Insert into runs table.
    from sqlalchemy import text
    db.execute(
        text("""
            INSERT OR IGNORE INTO runs (id, name, target_market, asset, horizon, day, scenario, notes, created_at)
            VALUES (:id, :name, :target_market, :asset, :horizon, :day, :scenario, :notes, :created_at)
        """),
        {
            "id": run_id,
            "name": run_name,
            "target_market": result.target_market,
            "asset": "SPY" if result.target_market == "US" else "BTCUSDT",
            "horizon": "Swing",
            "day": result.daily_decisions[0].date if result.daily_decisions else "",
            "scenario": "out-of-sample",
            "notes": notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    # 2. Insert a stub session row so that trades/equity_points FK to sessions
    #    is satisfied (trades.session_id references sessions.id).
    db.execute(
        text("""
            INSERT OR IGNORE INTO sessions
                (id, run_id, mode, target_market, asset, horizon, day,
                 max_turns, turns_used, consensus_action, final_action,
                 risk_status, risk_note, pnl, max_drawdown, win_rate)
            VALUES
                (:id, :run_id, :mode, :target_market, :asset, :horizon, :day,
                 0, 0, 'HOLD', 'HOLD', 'Approved', 'run stub', 0.0, 0.0, 0.0)
        """),
        {
            "id": run_id,
            "run_id": run_id,
            "mode": result.mode.value,
            "target_market": result.target_market,
            "asset": "SPY" if result.target_market == "US" else "BTCUSDT",
            "horizon": "Swing",
            "day": result.daily_decisions[0].date if result.daily_decisions else "",
        },
    )

    # 3. Persist daily decisions.
    for d in result.daily_decisions:
        row = DailyDecisionTable(
            run_id=run_id,
            date=d.date,
            target_market=d.target,
            mode=d.mode.value,
            consensus_action=d.consensus.value,
            final_action=d.final_action.value,
            risk_status=d.risk_status.value,
            risk_note=d.reason,
            fill_price=d.fill_price,
            position_held=d.position_held,
        )
        db.add(row)

    # 4. Persist trades.
    for trade in result.trades:
        row = TradeTable(
            session_id=run_id,
            entry_time=trade.entry,
            exit_time=trade.exit,
            side=trade.side.value,
            market=trade.market,
            pnl=trade.pnl,
            note=trade.note,
        )
        db.add(row)

    # 5. Persist equity curve.
    for idx, pt in enumerate(result.equity_curve):
        row = EquityPointTable(
            session_id=run_id,
            point_order=idx,
            label=pt.t,
            equity=pt.v,
        )
        db.add(row)

    db.commit()
    return run_id
