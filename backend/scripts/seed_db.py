"""
Database Seed Script.
Seeds market registry rows from markets.yaml.
"""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config.settings import DB_PATH


def main() -> None:
    markets_yaml = BASE_DIR / "app" / "config" / "markets.yaml"
    if not markets_yaml.exists():
        raise FileNotFoundError("markets.yaml missing.")

    data = yaml.safe_load(markets_yaml.read_text(encoding="utf-8")).get("markets", {})
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        for mid, m in data.items():
            cursor.execute(
                """
                INSERT OR REPLACE INTO markets (id, name, region, assets_json, is_open, why)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    mid,
                    m["name"],
                    m["region"],
                    json.dumps(m["assets"]),
                    1 if m.get("open", False) else 0,
                    m["why"],
                ),
            )
        conn.commit()
        print(f"Seeded {len(data)} markets into database.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
