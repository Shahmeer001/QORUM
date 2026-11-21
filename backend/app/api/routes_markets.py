from __future__ import annotations

from typing import Dict, List
from fastapi import APIRouter
from app.api.schemas import MarketInfoSchema
from app.modes.runner import load_markets_config

router = APIRouter(prefix="/markets", tags=["Markets"])


@router.get("", response_model=List[MarketInfoSchema])
def get_markets() -> List[MarketInfoSchema]:
    cfg = load_markets_config()
    res: List[MarketInfoSchema] = []
    for mid, m in cfg.items():
        res.append(
            MarketInfoSchema(
                id=mid,
                name=m["name"],
                region=m["region"],
                assets=m["assets"],
                open=m.get("open", False),
                why=m["why"],
            )
        )
    return res
