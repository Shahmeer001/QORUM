from app.config.settings import TURN_CAP
from app.supervisor.debate_loop import DebateLoop
from app.board.memory_repo import MemoryBoardRepository


def test_debate_turn_cap_enforced():
    loop = DebateLoop(agents={}, board=MemoryBoardRepository(), max_turns=10)
    assert loop.max_turns <= TURN_CAP
