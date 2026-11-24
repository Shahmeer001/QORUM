-- QUORUM Database Schema
-- SQLite3 Compatible

PRAGMA foreign_keys = ON;

-- Markets Registry
CREATE TABLE IF NOT EXISTS markets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT NOT NULL,
    assets_json TEXT NOT NULL,
    is_open INTEGER NOT NULL DEFAULT 1,
    why TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily / High-resolution Candles
CREATE TABLE IF NOT EXISTS candles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    quote_volume REAL DEFAULT 0.0,
    FOREIGN KEY (market_id) REFERENCES markets(id)
);
CREATE INDEX IF NOT EXISTS idx_candles_market_symbol_time ON candles(market_id, symbol, timestamp);

-- Decision Runs (contains 1 or more sessions across modes: Single, Silent, Debate)
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    target_market TEXT NOT NULL,
    asset TEXT NOT NULL,
    horizon TEXT NOT NULL DEFAULT 'Swing',
    day TEXT NOT NULL,
    scenario TEXT NOT NULL DEFAULT 'neutral', -- 'bull', 'bear', 'neutral'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily Decisions within a simulation run (Part 0.5)
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

-- Individual Sessions
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    run_id TEXT,
    mode TEXT NOT NULL, -- 'single', 'silent', 'debate'
    target_market TEXT NOT NULL,
    asset TEXT NOT NULL,
    horizon TEXT NOT NULL DEFAULT 'Swing',
    day TEXT NOT NULL,
    max_turns INTEGER NOT NULL DEFAULT 3,
    turns_used INTEGER NOT NULL DEFAULT 0,
    consensus_action TEXT NOT NULL, -- 'BUY', 'SELL', 'HOLD', 'ABSTAIN'
    final_action TEXT NOT NULL,     -- 'BUY', 'SELL', 'HOLD', 'ABSTAIN'
    risk_status TEXT NOT NULL,     -- 'Approved', 'Overridden', 'Rejected'
    risk_note TEXT,
    pnl REAL DEFAULT 0.0,
    max_drawdown REAL DEFAULT 0.0,
    win_rate REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

-- Debate and Recommendation Messages
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    round INTEGER NOT NULL,
    from_market TEXT NOT NULL,
    to_market TEXT NOT NULL, -- Market ID or 'BOARD'
    msg_type TEXT NOT NULL,  -- 'RECOMMEND', 'CHALLENGE', 'REPLY', 'FINAL'
    position TEXT NOT NULL,  -- 'BUY', 'SELL', 'HOLD', 'ABSTAIN'
    confidence REAL NOT NULL DEFAULT 50.0,
    reason TEXT NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '[]',
    is_visible INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
CREATE INDEX IF NOT EXISTS idx_messages_session_round ON messages(session_id, round);

-- Board Immutability Triggers: Reject edits and deletes at the SQLite engine level
CREATE TRIGGER IF NOT EXISTS prevent_message_update
BEFORE UPDATE ON messages
BEGIN
    SELECT RAISE(ABORT, 'QUORUM Board: Message updates are prohibited (append-only board).');
END;

CREATE TRIGGER IF NOT EXISTS prevent_message_delete
BEFORE DELETE ON messages
BEGIN
    SELECT RAISE(ABORT, 'QUORUM Board: Message deletions are prohibited (append-only board).');
END;

-- Supervisor Events Log
CREATE TABLE IF NOT EXISTS supervisor_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    round INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Agent Summaries per Session
CREATE TABLE IF NOT EXISTS agent_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    market_id TEXT NOT NULL,
    role TEXT NOT NULL, -- 'CHOSEN', 'RELATED'
    initial_action TEXT NOT NULL,
    final_action TEXT NOT NULL,
    confidence REAL NOT NULL,
    reason TEXT NOT NULL,
    detail TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (market_id) REFERENCES markets(id)
);

-- Agent Weights History
CREATE TABLE IF NOT EXISTS agent_weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    market_id TEXT NOT NULL,
    weight REAL NOT NULL,
    accuracy_score REAL NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (market_id) REFERENCES markets(id)
);

-- Trades generated by Simulation
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    entry_time TEXT NOT NULL,
    exit_time TEXT NOT NULL,
    side TEXT NOT NULL,
    market TEXT NOT NULL,
    pnl REAL NOT NULL,
    note TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Equity Curve Points
CREATE TABLE IF NOT EXISTS equity_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    point_order INTEGER NOT NULL,
    label TEXT NOT NULL,
    equity REAL NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Risk Events Log
CREATE TABLE IF NOT EXISTS risk_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    level TEXT NOT NULL, -- 'ok', 'warn', 'override'
    description TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
