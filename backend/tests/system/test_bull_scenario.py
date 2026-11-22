from collections import defaultdict
from app.domain.enums import Action, RiskStatus
from app.domain.models import SessionConfig
from app.services.session_service import SessionService
from app.supervisor.accuracy import AccuracyTracker


def test_bull_scenario_produces_valid_session():
    service = SessionService(db=None)
    cfg = SessionConfig(scenario="bull", target="GOLD", asset="XAUUSD")
    res = service.run_session(cfg)

    # 1. Structure validity
    assert len(res.messages) > 0
    assert 1 <= res.turns_used <= 3

    # 2. Agents lean BUY in a bull trend
    buy_agents = [a for a in res.agents if a.final == Action.BUY]
    assert len(buy_agents) >= 3, f"Expected majority of agents to recommend BUY in bull scenario, got: {[a.final.value for a in res.agents]}"

    # 3. Hand-computed weighted vote matches consensus
    tracker = AccuracyTracker()
    hand_scores = defaultdict(float)
    for a in res.agents:
        weight = tracker.get_weight(a.market, a.role)
        hand_scores[a.final] += weight * (a.confidence / 100.0)
    
    expected_consensus = max(hand_scores.keys(), key=lambda k: hand_scores[k])
    assert res.consensus == Action.BUY, f"Expected consensus BUY, got {res.consensus}"
    assert res.consensus == expected_consensus, f"Consensus {res.consensus} does not match hand-computed vote {expected_consensus}"

    # 4. Zero risk override fires (bull market satisfies risk parameters)
    assert res.risk_status == RiskStatus.APPROVED
    assert res.final_action == Action.BUY

    # 5. Trade execution and profit sign matches price move
    assert len(res.trades) > 0
    assert res.trades[0].side == "BUY"
    assert res.trades[0].pnl > 0.0, f"Expected positive trade PnL on upward bull trend, got {res.trades[0].pnl}"
    assert res.pnl > 0.0, f"Expected net positive session PnL, got {res.pnl}"
