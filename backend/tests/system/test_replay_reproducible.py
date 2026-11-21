from app.domain.models import SessionConfig
from app.services.session_service import SessionService


def test_replay_reproducibility():
    service = SessionService(db=None)
    cfg = SessionConfig(scenario="bull", target="GOLD", asset="XAUUSD")

    res1 = service.run_session(cfg)
    res2 = service.run_session(cfg)

    assert res1.consensus == res2.consensus
    assert res1.final_action == res2.final_action
    assert len(res1.messages) == len(res2.messages)
