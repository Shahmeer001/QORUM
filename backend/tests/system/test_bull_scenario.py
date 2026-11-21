from app.domain.enums import Action, RiskStatus
from app.domain.models import SessionConfig
from app.services.session_service import SessionService


def test_bull_scenario_produces_valid_session():
    service = SessionService(db=None)
    cfg = SessionConfig(scenario="bull", target="GOLD", asset="XAUUSD")
    res = service.run_session(cfg)
    assert res.pnl >= 0.0
    assert len(res.messages) > 0
    assert res.turns_used <= 3
