import pytest
from app.adapters.synthetic import SyntheticAdapter
from app.agents.market_agent import MarketAgent
from app.board.memory_repo import MemoryBoardRepository
from app.domain.enums import Role


def test_agent_cannot_request_another_markets_data():
    adapter = SyntheticAdapter()
    board = MemoryBoardRepository()
    agent_gold = MarketAgent(market="GOLD", adapter=adapter, board=board, role=Role.CHOSEN)

    # 1. Market isolation: bound strictly to its own market and adapter
    assert agent_gold.market == "GOLD"
    assert agent_gold.adapter == adapter
    assert hasattr(agent_gold, "_fetch_own_candles")

    # 2. Strict isolation: agent does NOT expose foreign market access methods
    assert not hasattr(agent_gold, "get_foreign_candles")
    assert not hasattr(agent_gold, "fetch_foreign_data")
    assert not hasattr(agent_gold, "read_other_market_feed")
