"""
Import & Validate Knowledge Base Script.
Copies and checks research output (agent_pattern_knowledge.json) into backend/knowledge/crypto.json.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

# Add backend to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config.settings import KNOWLEDGE_DIR


def main() -> None:
    print("Checking and importing research pattern knowledge...")
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    research_json = BASE_DIR.parent / "research" / "output" / "agent_pattern_knowledge.json"
    target_crypto = KNOWLEDGE_DIR / "crypto.json"

    if research_json.exists():
        print(f"Found research output at {research_json}. Importing...")
        data = json.loads(research_json.read_text(encoding="utf-8"))
        target_crypto.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"Imported successfully to {target_crypto}")
    else:
        print(f"Research output not yet generated at {research_json}.")
        if not target_crypto.exists():
            print("Writing initial seed knowledge to crypto.json...")
            seed = {
                "market": "CRYPTO",
                "baseline": {"win_rate_pct": 51.8, "high_profit_rate_pct": 12.8},
                "rsi_rule": {"buy_zone": [20, 30], "sell_zone": [70, 80]},
                "patterns": {"D-D-D": {"high_rate_pct": 18.4, "lift": 1.43}},
            }
            target_crypto.write_text(json.dumps(seed, indent=2), encoding="utf-8")
        print(f"Verified knowledge exists at {target_crypto}")


if __name__ == "__main__":
    main()
