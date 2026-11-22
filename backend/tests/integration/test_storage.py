import sqlite3
import tempfile
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.board.sql_repo import SqlBoardRepository
from app.db.tables import Base
from app.domain.enums import Action, MsgType
from app.domain.models import Message


@pytest.fixture
def test_db_path(tmp_path: Path):
    db_file = tmp_path / "test_storage.db"
    schema_file = Path(__file__).resolve().parent.parent.parent.parent / "db" / "schema.sql"
    
    conn = sqlite3.connect(db_file)
    conn.executescript(schema_file.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()
    return db_file


def test_sql_repo_persists_across_connections(test_db_path: Path):
    """
    Test that SqlBoardRepository persists messages across completely separate DB connections.
    """
    db_url = f"sqlite:///{test_db_path}"
    engine1 = create_engine(db_url)
    Session1 = sessionmaker(bind=engine1)
    
    msg = Message(
        id="msg_test_persist_123",
        session_id="session_persist_abc",
        round=1,
        from_market="GOLD",
        to_market="BOARD",
        msg_type=MsgType.RECOMMEND,
        position=Action.BUY,
        confidence=85.0,
        reason="Storage persistence validation test",
        evidence=["Pattern: Bullish engulfing", "RSI: 34.2"],
    )

    # 1. Connection 1: write message and close connection
    session1 = Session1()
    repo1 = SqlBoardRepository(session1)
    repo1.add_message(msg)
    session1.close()
    engine1.dispose()

    # 2. Connection 2: fresh engine and session to verify persistence
    engine2 = create_engine(db_url)
    Session2 = sessionmaker(bind=engine2)
    session2 = Session2()
    repo2 = SqlBoardRepository(session2)

    messages = repo2.get_messages("session_persist_abc")
    session2.close()
    engine2.dispose()

    assert len(messages) == 1
    loaded = messages[0]
    assert loaded.id == "msg_test_persist_123"
    assert loaded.session_id == "session_persist_abc"
    assert loaded.from_market == "GOLD"
    assert loaded.position == Action.BUY
    assert loaded.confidence == 85.0
    assert loaded.reason == "Storage persistence validation test"
    assert loaded.evidence == ["Pattern: Bullish engulfing", "RSI: 34.2"]


def test_sql_board_rejects_edits_and_deletes_at_db_level(test_db_path: Path):
    """
    Test that the board rejects edits and deletes at both the Python repo level
    and at the database level via SQLite ABORT triggers.
    """
    db_url = f"sqlite:///{test_db_path}"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    repo = SqlBoardRepository(session)

    msg = Message(
        id="msg_immutable_1",
        session_id="session_immutability",
        round=0,
        from_market="US",
        to_market="BOARD",
        msg_type=MsgType.RECOMMEND,
        position=Action.HOLD,
        reason="Initial stance",
    )
    repo.add_message(msg)

    # 1. Python repo interface rejection
    with pytest.raises(PermissionError):
        repo.update_message(msg)

    with pytest.raises(PermissionError):
        repo.delete_message("msg_immutable_1")

    session.close()

    # 2. Database level rejection: triggers raise SQLite exceptions
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    with pytest.raises(sqlite3.DatabaseError) as exc_update:
        cursor.execute(
            "UPDATE messages SET reason = 'Tampered text' WHERE id = 'msg_immutable_1'"
        )
    assert "Message updates are prohibited" in str(exc_update.value)

    with pytest.raises(sqlite3.DatabaseError) as exc_delete:
        cursor.execute(
            "DELETE FROM messages WHERE id = 'msg_immutable_1'"
        )
    assert "Message deletions are prohibited" in str(exc_delete.value)

    conn.close()


def test_init_db_creates_all_tables_from_schema(tmp_path: Path):
    """
    Test that database initialization script / schema.sql creates all 11 required tables.
    """
    test_db = tmp_path / "schema_check.db"
    schema_file = Path(__file__).resolve().parent.parent.parent.parent / "db" / "schema.sql"
    
    assert schema_file.exists()
    sql_text = schema_file.read_text(encoding="utf-8")

    conn = sqlite3.connect(test_db)
    conn.executescript(sql_text)
    conn.commit()

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}

    expected_tables = {
        "markets",
        "candles",
        "runs",
        "sessions",
        "messages",
        "supervisor_events",
        "agent_summaries",
        "agent_weights",
        "trades",
        "equity_points",
        "risk_events",
    }

    missing_tables = expected_tables - tables
    assert not missing_tables, f"Missing tables in SQLite DB: {missing_tables}"

    # Verify triggers were created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger';")
    triggers = {row[0] for row in cursor.fetchall()}
    assert "prevent_message_update" in triggers
    assert "prevent_message_delete" in triggers

    conn.close()
