from app.domain.enums import Action, RiskStatus
from app.domain.models import Candle
from app.risk.risk_layer import RiskLayer


def test_risk_overrides_high_volatility():
    risk = RiskLayer(max_volatility=2.0)
    # High volatility candles (> 2.0% return std)
    volatile_candles = [
        Candle(timestamp="t", open=100, high=110, low=90, close=100 + (10 if i % 2 == 0 else -10), volume=100)
        for i in range(20)
    ]

    action, status, note, events = risk.evaluate(Action.BUY, volatile_candles)[:4]
    assert action == Action.HOLD
    assert status == RiskStatus.OVERRIDDEN
    assert "volatility" in note.lower()
