"""
Persistence helpers for simulation runs (Part 0.5).

The replay simulator returns a SimulationResult with daily_decisions, trades,
equity_curve, and risk_events. This module persists them to SQLite so the
experiment run can be audited later via the DB.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.tables import DailyDecisionTable
from app.simulator.replay_simulator import DailyDecisionRecord, SimulationResult


def persist_run(
    db: Session,
    result: SimulationResult,
    run_name: str,
    notes: str = "",
) -> str:
    """
    Persist a simulation result as a run with its daily decisions.
    Returns the run_id.
    """
    run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{result.target_market}-{result.mode.value}"
    # Insert into runs table (minimal; runs table schema is simple)
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

    # Persist daily decisions
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

    db.commit()
    return run_id
