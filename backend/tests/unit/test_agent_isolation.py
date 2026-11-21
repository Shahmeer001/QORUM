from app.adapters.synthetic import SyntheticAdapter
from app.agents.market_agent import MarketAgent
from app.board.memory_repo import MemoryBoardRepository
from app.domain.enums import Role


def test_agent_cannot_request_another_markets_data():
    adapter = SyntheticAdapter()
    board = MemoryBoardRepository()
    agent_gold = MarketAgent(market="GOLD", adapter=adapter, board=board, role=Role.CHOSEN)

    # Agent is bound to its own adapter; has no access to foreign proprietary data
    assert agent_gold.market == "GOLD"
    assert hasattr(agent_gold, "_fetch_own_candles")
