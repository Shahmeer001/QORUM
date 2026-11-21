from app.domain.enums import Action, RiskStatus
from app.domain.models import SessionConfig
from app.services.session_service import SessionService


def test_bear_scenario_triggers_risk_override():
    service = SessionService(db=None)
    cfg = SessionConfig(scenario="bear", target="GOLD", asset="XAUUSD", max_vol=2.0)
    res = service.run_session(cfg)
    # Elevated volatility should trigger override to HOLD
    assert res.risk_status == RiskStatus.OVERRIDDEN
    assert res.final_action == Action.HOLD
