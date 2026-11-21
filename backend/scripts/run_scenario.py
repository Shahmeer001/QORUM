"""
CLI Scenario Runner.
Runs bull or bear scenario directly from the terminal.
Usage:
  python scripts/run_scenario.py --scenario bull
  python scripts/run_scenario.py --scenario bear
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.domain.enums import Mode
from app.domain.models import SessionConfig
from app.services.session_service import SessionService


def main() -> None:
    parser = argparse.ArgumentParser(description="Run QUORUM Scenario")
    parser.add_argument("--scenario", choices=["bull", "bear", "neutral"], default="bull")
    parser.add_argument("--mode", choices=["single", "silent", "debate"], default="debate")
    parser.add_argument("--target", default="GOLD")
    parser.add_argument("--asset", default="XAUUSD")
    args = parser.parse_args()

    print(f"\n==========================================")
    print(f"  RUNNING QUORUM SCENARIO: {args.scenario.upper()} ({args.mode.upper()})")
    print(f"==========================================\n")

    cfg = SessionConfig(
        target=args.target,
        asset=args.asset,
        scenario=args.scenario,
        mode=Mode(args.mode),
    )
    service = SessionService(db=None)
    result = service.run_session(cfg)

    print(f"Session ID:      {result.id}")
    print(f"Target Asset:    {result.asset} ({result.target})")
    print(f"Turns Used:      {result.turns_used} / {result.max_turns}")
    print(f"Consensus:       {result.consensus.value}")
    print(f"Final Action:    {result.final_action.value}")
    print(f"Risk Status:     {result.risk_status.value}")
    print(f"Risk Note:       {result.risk_note}")
    print(f"Simulated PnL:   +{result.pnl:.2f}%")
    print(f"Max Drawdown:    -{result.max_drawdown:.2f}%")
    print(f"Total Messages:  {len(result.messages)}")
    print("\n--- Agent Final Positions ---")
    for a in result.agents:
        print(f"  [{a.market:6}] {a.final.value:5} ({a.confidence:.0f}% conf) - {a.reason}")


if __name__ == "__main__":
    main()
