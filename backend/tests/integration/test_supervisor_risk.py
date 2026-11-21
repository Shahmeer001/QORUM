from app.adapters.synthetic import SyntheticAdapter
from app.domain.enums import Action, RiskStatus
from app.risk.risk_layer import RiskLayer
from app.supervisor.accuracy import AccuracyTracker
from app.supervisor.consensus import calculate_consensus
from app.domain.models import AgentSummary
from app.domain.enums import Role


def test_supervisor_consensus_and_risk_veto():
    tracker = AccuracyTracker()
    summaries = [
        AgentSummary(market="GOLD", role=Role.CHOSEN, initial=Action.BUY, final=Action.BUY, confidence=80, reason="Strong", detail=""),
        AgentSummary(market="US", role=Role.RELATED, initial=Action.BUY, final=Action.BUY, confidence=70, reason="Inflow", detail=""),
    ]
    consensus, conf, _ = calculate_consensus(summaries, tracker)
    assert consensus == Action.BUY

    # Feed high volatility candles
    risk = RiskLayer(max_volatility=1.5)
    candles = SyntheticAdapter(scenario="bear").get_candles(limit=20)
    final_action, status, _, _ = risk.evaluate(consensus, candles)
    assert status == RiskStatus.OVERRIDDEN
    assert final_action == Action.HOLD
