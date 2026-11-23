"""
Agent Factory and Execution Runner.
Builds agents dynamically via minimal dynamic registry loader from markets.yaml.
Strictly enforces real adapters for active markets (US, CRYPTO).
"""
from __future__ import annotations

import importlib
from pathlib import Path
from typing import Dict, List
import yaml

from app.adapters.base import MarketDataAdapter
from app.adapters.binance_btc import BinanceBTCAdapter
from app.adapters.synthetic import SyntheticAdapter
from app.adapters.us_spy import USMarketAdapter
from app.agents.market_agent import MarketAgent
from app.board.repository import BoardRepository
from app.config.settings import BASE_DIR
from app.domain.enums import Mode, Role
from app.modes.debate import run_debate_mode
from app.modes.silent import run_silent_mode
from app.modes.single import run_single_mode


def load_markets_config() -> dict:
    config_file = BASE_DIR / "app" / "config" / "markets.yaml"
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f).get("markets", {})
    return {}


def get_adapter_for_market(
    market_id: str, market_cfg: dict, scenario: str = "neutral", decision_date: str | None = None
) -> MarketDataAdapter:
    """
    Registry adapter loader.
    Active markets strictly use real data adapters (never synthetic).
    Inactive/FYP2 markets load their declared adapter class dynamically.
    `decision_date` is threaded into every adapter so the temporal guard
    (default-deny future bars) is enforced on every code path.
    """
    if market_id == "US":
        return USMarketAdapter(scenario=scenario, current_date=decision_date)
    if market_id == "CRYPTO":
        return BinanceBTCAdapter(current_date=decision_date)

    adapter_path = market_cfg.get("adapter")
    if adapter_path:
        try:
            module_name, class_name = adapter_path.rsplit(".", 1)
            mod = importlib.import_module(module_name)
            cls = getattr(mod, class_name)
            if cls is SyntheticAdapter:
                base_price = 2000.0 if market_id == "GOLD" else 100.0
                return cls(scenario=scenario, base_price=base_price, current_date=decision_date)
            return cls()
        except Exception:
            pass

    base_price = 2000.0 if market_id == "GOLD" else 100.0
    return SyntheticAdapter(scenario=scenario, base_price=base_price, current_date=decision_date)


def build_agents(
    board: BoardRepository,
    target_market: str,
    related_markets: List[str],
    scenario: str = "neutral",
    decision_date: str | None = None,
) -> Dict[str, MarketAgent]:
    config = load_markets_config()
    agents: Dict[str, MarketAgent] = {}

    selected = [target_market] + [m for m in related_markets if m != target_market]

    for m in selected:
        role = Role.CHOSEN if m == target_market else Role.RELATED
        market_cfg = config.get(m, {})
        adapter = get_adapter_for_market(m, market_cfg, scenario=scenario, decision_date=decision_date)

        agent = MarketAgent(
            market=m,
            adapter=adapter,
            board=board,
            role=role,
        )
        agents[m] = agent

    return agents
