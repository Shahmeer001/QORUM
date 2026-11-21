from app.domain.enums import Mode
from app.domain.models import SessionConfig
from app.services.session_service import SessionService


def test_silent_vs_debate_differ():
    service = SessionService(db=None)
    cfg_silent = SessionConfig(mode=Mode.SILENT, target="GOLD", asset="XAUUSD", scenario="bull")
    cfg_debate = SessionConfig(mode=Mode.DEBATE, target="GOLD", asset="XAUUSD", scenario="bull")

    res_silent = service.run_session(cfg_silent)
    res_debate = service.run_session(cfg_debate)

    # Silent mode has 0 turns used and only initial round messages
    assert res_silent.turns_used == 0
    assert res_debate.turns_used >= 1
    assert len(res_debate.messages) > len(res_silent.messages)
