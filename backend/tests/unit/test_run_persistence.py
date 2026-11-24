"""
Tests for Part 0.5: persisting experiment runs to the database.
"""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.tables import Base
from app.domain.enums import Action, Mode, RiskStatus
from app.simulator.replay_simulator import DailyDecisionRecord, SimulationResult
from app.services.run_persistence import persist_run


def test_persist_run_stores_daily_decisions():
    # Create a fresh DB with the schema.
    schema_file = Path(__file__).resolve().parent.parent.parent.parent / "db" / "schema.sql"
    assert schema_file.exists()
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_file.close()
    conn = sqlite3.connect(db_file.name)
    conn.executescript(schema_file.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()

    engine = create_engine(f"sqlite:///{db_file.name}")
    Session = sessionmaker(bind=engine)
    session = Session()

    # Build a minimal SimulationResult.
    result = SimulationResult(
        target_market="US",
        mode=Mode.DEBATE,
        allow_short=False,
        initial_capital=10000.0,
        final_equity=10500.0,
        pnl_dollars=500.0,
        pnl_pct=5.0,
        max_drawdown_pct=2.0,
        hit_rate_pct=60.0,
        exposure_pct=75.0,
        buy_hold_exposure_scaled_return_pct=3.0,
        sharpe_ratio=1.2,
        trade_count=5,
        turnover=1.5,
        evaluation_days_count=3,
        degraded_days_count=0,
        trades=[],
        equity_curve=[],
        daily_decisions=[
            DailyDecisionRecord(
                date="2025-01-06",
                target="US",
                mode=Mode.DEBATE,
                consensus=Action.BUY,
                final_action=Action.BUY,
                risk_status=RiskStatus.APPROVED,
                reason="Risk control approved BUY",
                fill_price=450.0,
                position_held=1,
            ),
            DailyDecisionRecord(
                date="2025-01-07",
                target="US",
                mode=Mode.DEBATE,
                consensus=Action.HOLD,
                final_action=Action.HOLD,
                risk_status=RiskStatus.APPROVED,
                reason="Flat",
                fill_price=None,
                position_held=0,
            ),
        ],
        degraded_days=[],
        benchmark_buy_hold_return_pct=4.0,
        benchmark_buy_hold_entry_price=440.0,
        benchmark_buy_hold_entry_date="2025-01-06",
        benchmark_buy_hold_exit_price=460.0,
        benchmark_buy_hold_exit_date="2025-01-08",
        max_entry_leverage_ratio=1.0,
        max_gross_exposure_ratio=1.0,
        final_accuracy={"US": 0.55},
    )

    run_id = persist_run(session, result, run_name="test-run", notes="unit test")
    assert run_id.startswith("run-")
    assert "US" in run_id and "debate" in run_id.lower()

    # Verify rows inserted.
    from sqlalchemy import text
    rows = session.execute(text("SELECT COUNT(*) FROM daily_decisions WHERE run_id = :rid"), {"rid": run_id}).scalar()
    assert rows == 2

    # Cleanup.
    session.close()
    engine.dispose()
    Path(db_file.name).unlink()
