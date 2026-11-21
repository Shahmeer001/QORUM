"""
Agent Factory and Execution Runner.
Builds agents dynamically from markets.yaml and runs the chosen mode.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import yaml

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


def build_agents(
    board: BoardRepository,
    target_market: str,
    related_markets: List[str],
    scenario: str = "neutral",
) -> Dict[str, MarketAgent]:
    config = load_markets_config()
    agents: Dict[str, MarketAgent] = {}

    selected = [target_market] + [m for m in related_markets if m != target_market]

    for m in selected:
        role = Role.CHOSEN if m == target_market else Role.RELATED
        # Assign specialized adapters
        if m == "CRYPTO":
            adapter = BinanceBTCAdapter()
        elif m in ("US", "FOREX"):
            adapter = USMarketAdapter(scenario=scenario)
        else:
            adapter = SyntheticAdapter(scenario=scenario, base_price=2000.0 if m == "GOLD" else 100.0)

        agent = MarketAgent(
            market=m,
            adapter=adapter,
            board=board,
            role=role,
        )
        agents[m] = agent

    return agents
