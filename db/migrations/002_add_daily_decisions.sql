-- Migration 002: Add daily_decisions table (Part 0.5)
-- Apply with: python backend/scripts/init_db.py  OR  sqlite3 backend/quorum.db < db/migrations/002_add_daily_decisions.sql

CREATE TABLE IF NOT EXISTS daily_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    date TEXT NOT NULL,
    target_market TEXT NOT NULL,
    mode TEXT NOT NULL,
    consensus_action TEXT NOT NULL,
    final_action TEXT NOT NULL,
    risk_status TEXT NOT NULL,
    risk_note TEXT,
    fill_price REAL,
    position_held INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);
CREATE INDEX IF NOT EXISTS idx_daily_decisions_run ON daily_decisions(run_id, date);
