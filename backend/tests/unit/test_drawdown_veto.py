"""
Tests for Part 0.3: Drawdown veto in RiskLayer.
"""
from app.domain.enums import Action, RiskStatus
from app.domain.models import Candle
from app.risk.risk_layer import RiskLayer


def test_drawdown_above_max_forces_hold():
    """If running drawdown exceeds max_drawdown, the risk layer forces HOLD."""
    risk = RiskLayer(max_volatility=10.0, max_drawdown=5.0)  # generous vol, tight DD

    # Low-volatility candles so the volatility check does not fire.
    calm_candles = [
        Candle(timestamp=f"t{i}", open=100, high=101, low=99, close=100, volume=1000)
        for i in range(20)
    ]

    action, status, note, events = risk.evaluate(
        consensus=Action.BUY,
        candles=calm_candles,
        running_drawdown_pct=6.0,  # exceeds 5% limit
    )
    assert action == Action.HOLD
    assert status == RiskStatus.OVERRIDDEN
    assert "Drawdown" in note and "forced HOLD" in note
    assert any(e.level == "override" and "Drawdown" in e.text for e in events)


def test_drawdown_within_limit_allows_buy():
    """If running drawdown is within the limit, BUY is approved (volatility permitting)."""
    risk = RiskLayer(max_volatility=10.0, max_drawdown=5.0)

    calm_candles = [
        Candle(timestamp=f"t{i}", open=100, high=101, low=99, close=100, volume=1000)
        for i in range(20)
    ]

    action, status, note, events = risk.evaluate(
        consensus=Action.BUY,
        candles=calm_candles,
        running_drawdown_pct=3.0,  # within limit
    )
    assert action == Action.BUY
    assert status == RiskStatus.APPROVED


def test_drawdown_veto_takes_precedence_over_volatility():
    """If both drawdown and volatility breach, drawdown veto fires first."""
    risk = RiskLayer(max_volatility=2.0, max_drawdown=5.0)

    # High-volatility candles that would trigger vol veto on their own.
    volatile_candles = [
        Candle(timestamp=f"t{i}", open=100, high=110, low=90, close=100 + (10 if i % 2 == 0 else -10), volume=1000)
        for i in range(20)
    ]

    action, status, note, events = risk.evaluate(
        consensus=Action.BUY,
        candles=volatile_candles,
        running_drawdown_pct=6.0,  # drawdown breach
    )
    # Drawdown check runs first; result is HOLD from drawdown, not vol.
    assert action == Action.HOLD
    assert "Drawdown" in note
