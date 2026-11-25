"""
Tests for Part 0.5 / Item 5: persisting experiment runs to the database.
"""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.tables import Base
from app.domain.enums import Action, Mode, RiskStatus
from app.domain.models import EquityPoint, Trade
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

    # Build a minimal SimulationResult with trades and equity curve.
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
        trades=[
            Trade(
                entry="2025-01-06 09:30:00-05:00",
                exit="2025-01-07 09:30:00-05:00",
                side=Action.BUY,
                market="US",
                pnl=120.0,
                note="Long entry",
            ),
        ],
        equity_curve=[
            EquityPoint(t="2025-01-06", v=10000.0),
            EquityPoint(t="2025-01-07", v=10120.0),
        ],
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
            DailyDecisionRecord(
                date="2025-01-08",
                target="US",
                mode=Mode.DEBATE,
                consensus=Action.BUY,
                final_action=Action.HOLD,
                risk_status=RiskStatus.OVERRIDDEN,
                reason="Drawdown (6.00%) breached limit (5.0%). Risk forced HOLD.",
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

    from sqlalchemy import text
    # Verify daily_decisions rows inserted.
    dd_rows = session.execute(
        text("SELECT COUNT(*) FROM daily_decisions WHERE run_id = :rid"), {"rid": run_id}
    ).scalar()
    assert dd_rows == 3

    # Verify trades rows inserted (Item 5).
    trade_rows = session.execute(
        text("SELECT COUNT(*) FROM trades WHERE session_id = :sid"), {"sid": run_id}
    ).scalar()
    assert trade_rows == 1, f"Expected 1 trade row, got {trade_rows}"

    # Verify equity_points rows inserted (Item 5).
    eq_rows = session.execute(
        text("SELECT COUNT(*) FROM equity_points WHERE session_id = :sid"), {"sid": run_id}
    ).scalar()
    assert eq_rows == 2, f"Expected 2 equity_point rows, got {eq_rows}"

    # Verify risk_events rows inserted for OVERRIDDEN decisions (task (c)).
    re_rows = session.execute(
        text("SELECT COUNT(*) FROM risk_events WHERE session_id = :sid"), {"sid": run_id}
    ).scalar()
    assert re_rows == 1, f"Expected 1 risk_event row for the overridden day, got {re_rows}"

    # Cleanup.
    session.close()
    engine.dispose()
    Path(db_file.name).unlink()
