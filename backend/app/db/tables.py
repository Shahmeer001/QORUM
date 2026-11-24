"""
SQLAlchemy ORM Table Definitions.
Mirrors db/schema.sql.
"""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text, DateTime
from app.db.connection import Base


def utc_now():
    return datetime.now(timezone.utc)


class MarketTable(Base):
    __tablename__ = "markets"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    region = Column(String, nullable=False)
    assets_json = Column(Text, nullable=False)
    is_open = Column(Integer, default=1)
    why = Column(Text, nullable=False)


class RunTable(Base):
    __tablename__ = "runs"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    target_market = Column(String, nullable=False)
    asset = Column(String, nullable=False)
    horizon = Column(String, default="Swing")
    day = Column(String, nullable=False)
    scenario = Column(String, default="neutral")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)


class SessionTable(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True)
    run_id = Column(String, nullable=True)
    mode = Column(String, nullable=False)
    target_market = Column(String, nullable=False)
    asset = Column(String, nullable=False)
    horizon = Column(String, default="Swing")
    day = Column(String, nullable=False)
    max_turns = Column(Integer, default=3)
    turns_used = Column(Integer, default=0)
    consensus_action = Column(String, nullable=False)
    final_action = Column(String, nullable=False)
    risk_status = Column(String, nullable=False)
    risk_note = Column(Text, nullable=True)
    pnl = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utc_now)


class MessageTable(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    round = Column(Integer, nullable=False)
    from_market = Column(String, nullable=False)
    to_market = Column(String, nullable=False)
    msg_type = Column(String, nullable=False)
    position = Column(String, nullable=False)
    confidence = Column(Float, default=50.0)
    reason = Column(Text, nullable=False)
    evidence_json = Column(Text, default="[]")
    is_visible = Column(Integer, default=1)
    created_at = Column(DateTime, default=utc_now)


class DailyDecisionTable(Base):
    __tablename__ = "daily_decisions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    date = Column(String, nullable=False)
    target_market = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    consensus_action = Column(String, nullable=False)
    final_action = Column(String, nullable=False)
    risk_status = Column(String, nullable=False)
    risk_note = Column(Text, nullable=True)
    fill_price = Column(Float, nullable=True)
    position_held = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)


class TradeTable(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    entry_time = Column(String, nullable=False)
    exit_time = Column(String, nullable=False)
    side = Column(String, nullable=False)
    market = Column(String, nullable=False)
    pnl = Column(Float, nullable=False)
    note = Column(Text, nullable=True)


class EquityPointTable(Base):
    __tablename__ = "equity_points"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    point_order = Column(Integer, nullable=False)
    label = Column(String, nullable=False)
    equity = Column(Float, nullable=False)
