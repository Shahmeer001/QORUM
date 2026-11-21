"""
Database Initialization Script.
Creates tables from db/schema.sql into SQLite.
"""
from __future__ import annotations

from pathlib import Path
import sqlite3
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config.settings import DB_PATH


def main() -> None:
    schema_file = BASE_DIR.parent / "db" / "schema.sql"
    print(f"Initializing SQLite database at: {DB_PATH}")
    print(f"Reading schema from: {schema_file}")

    if not schema_file.exists():
        raise FileNotFoundError(f"Missing schema file: {schema_file}")

    sql = schema_file.read_text(encoding="utf-8")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(sql)
        conn.commit()
        print("Database schema successfully applied.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
