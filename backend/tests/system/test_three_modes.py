from app.domain.enums import Mode
from app.domain.models import SessionConfig
from app.services.session_service import SessionService


def test_all_three_modes_execute_cleanly():
    service = SessionService(db=None)
    for m in [Mode.SINGLE, Mode.SILENT, Mode.DEBATE]:
        cfg = SessionConfig(mode=m, target="GOLD", asset="XAUUSD")
        res = service.run_session(cfg)
        assert res.mode == m
        assert res.final_action is not None
