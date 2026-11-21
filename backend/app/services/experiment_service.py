"""
Experiment Comparison Service.
Runs Single, Silent, and Debate configurations side-by-side on the same asset and scenario.
"""
from __future__ import annotations

from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.domain.enums import Mode, RiskStatus
from app.domain.models import SessionConfig
from app.services.session_service import SessionService


class ExperimentService:
    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def run_comparison(
        self,
        target: str = "GOLD",
        asset: str = "XAUUSD",
        day: str = "2026-11-10",
        scenario: str = "neutral",
    ) -> List[Dict[str, Any]]:
        service = SessionService(db=self.db)
        modes = [
            ("Single Agent", Mode.SINGLE),
            ("Silent Consensus", Mode.SILENT),
            ("Debate Mode", Mode.DEBATE),
        ]

        setups: List[Dict[str, Any]] = []
        for name, m in modes:
            cfg = SessionConfig(
                target=target,
                related=["PSX", "US", "FOREX", "CRYPTO"],
                asset=asset,
                day=day,
                scenario=scenario,
                mode=m,
            )
            res = service.run_session(cfg)
            setups.append({
                "name": name,
                "id": res.id,
                "mode": m.value,
                "markets": [target] if m == Mode.SINGLE else [target, "PSX", "US", "FOREX", "CRYPTO"],
                "action": res.final_action.value,
                "turns": res.turns_used,
                "override": res.risk_status == RiskStatus.OVERRIDDEN,
                "pnl": res.pnl,
                "drawdown": res.max_drawdown,
                "messages": len(res.messages),
            })

        return setups
