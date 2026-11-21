from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas import CompareSetupSchema
from app.services.experiment_service import ExperimentService

router = APIRouter(prefix="/compare", tags=["Compare"])


@router.get("", response_model=List[CompareSetupSchema])
def get_comparison_setups(
    target: str = "GOLD",
    asset: str = "XAUUSD",
    day: str = "2026-11-10",
    scenario: str = "neutral",
    db: Session = Depends(get_db),
) -> List[CompareSetupSchema]:
    service = ExperimentService(db=db)
    res = service.run_comparison(target=target, asset=asset, day=day, scenario=scenario)
    return [CompareSetupSchema(**r) for r in res]
