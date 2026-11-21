from app.adapters.synthetic import SyntheticAdapter
from app.agents.brains.fake_brain import FakeBrain
from app.agents.market_agent import MarketAgent
from app.board.memory_repo import MemoryBoardRepository
from app.domain.enums import Action, Role


def test_agent_board_interaction():
    board = MemoryBoardRepository()
    adapter = SyntheticAdapter()
    agent = MarketAgent(
        market="GOLD", adapter=adapter, board=board, role=Role.CHOSEN, brain=FakeBrain(Action.BUY)
    )

    msg = agent.round_0_recommend("session_test", "XAUUSD")
    assert msg.position == Action.BUY

    stored = board.get_messages("session_test")
    assert len(stored) == 1
    assert stored[0].id == msg.id
