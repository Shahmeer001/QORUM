"""
Item 1: Risk veto semantics tests.

Three scenarios are verified:
  (a) Consensus HOLD (APPROVED) keeps the current position — no trade appended.
  (b) Drawdown veto (OVERRIDDEN, veto_source="drawdown") flattens an open position —
      a SELL trade is appended.
  (c) After cool-off (drawdown_cooloff_days=1 so the test stays fast) a new BUY
      trade appears on the first post-cool-off day.
"""
from __future__ import annotations

import pandas as pd
import pytest

from app.domain.enums import Action, RiskStatus
from app.domain.models import Candle, RiskEvent
from app.risk.risk_layer import RiskLayer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _calm_candles(n: int = 20) -> list:
    return [
        Candle(timestamp=f"t{i}", open=100, high=101, low=99, close=100, volume=1000)
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# (a) Consensus HOLD keeps position: RiskLayer returns APPROVED with no veto.
# ---------------------------------------------------------------------------

def test_consensus_hold_approved_no_veto():
    """HOLD consensus with no drawdown/vol breach is approved with empty veto_source."""
    risk = RiskLayer(max_volatility=10.0, max_drawdown=5.0)
    action, status, note, events, veto_source = risk.evaluate(
        consensus=Action.HOLD,
        candles=_calm_candles(),
        running_drawdown_pct=0.0,
    )
    assert action == Action.HOLD
    assert status == RiskStatus.APPROVED
    assert veto_source == ""


# ---------------------------------------------------------------------------
# (b) Drawdown veto flattens position.
# ---------------------------------------------------------------------------

def test_drawdown_veto_source_is_drawdown():
    """Drawdown breach sets veto_source='drawdown' and forces HOLD."""
    risk = RiskLayer(max_volatility=10.0, max_drawdown=5.0)
    action, status, note, events, veto_source = risk.evaluate(
        consensus=Action.BUY,
        candles=_calm_candles(),
        running_drawdown_pct=6.0,  # above limit
    )
    assert action == Action.HOLD
    assert status == RiskStatus.OVERRIDDEN
    assert veto_source == "drawdown"
    assert any(e.level == "override" and "Drawdown" in e.text for e in events)


def test_volatility_veto_source_is_volatility():
    """Volatility breach sets veto_source='volatility'."""
    risk = RiskLayer(max_volatility=2.0, max_drawdown=50.0)
    volatile = [
        Candle(timestamp=f"t{i}", open=100, high=110, low=90,
               close=100 + (10 if i % 2 == 0 else -10), volume=1000)
        for i in range(20)
    ]
    action, status, note, events, veto_source = risk.evaluate(
        consensus=Action.BUY,
        candles=volatile,
        running_drawdown_pct=0.0,
    )
    assert action == Action.HOLD
    assert status == RiskStatus.OVERRIDDEN
    assert veto_source == "volatility"


# ---------------------------------------------------------------------------
# (c) Replay simulator: drawdown veto flattens position, cool-off blocks,
#     then resumes.  Uses a minimal _SmallSim driven by FakeBrain(BUY).
# ---------------------------------------------------------------------------

def _write_fixtures(tmp_path, closes):
    """Write SPY and BTC CSVs with the given close prices."""
    dates = [
        "2025-01-06", "2025-01-07", "2025-01-08",
        "2025-01-09", "2025-01-10", "2025-01-13",
        "2025-01-14", "2025-01-15", "2025-01-16",
        "2025-01-17", "2025-01-21", "2025-01-22",
        "2025-01-23", "2025-01-24", "2025-01-27",
    ][:len(closes)]
    spy_lines = ["Date,Open,High,Low,Close,Volume"]
    for d, c in zip(dates, closes):
        dd = f"{d[8:10]}/{d[5:7]}/{d[:4]}"
        spy_lines.append(f"{dd} 16:00:00,{c},{c+1},{c-1},{c},1000000")
    spy_path = tmp_path / "spy_veto.csv"
    spy_path.write_text("\n".join(spy_lines), encoding="utf-8")

    btc_lines = ["timestamp,Date,Open,High,Low,Close,Volume,QuoteVolume,Trades"]
    start = pd.Timestamp("2025-01-06 00:00:00+00:00")
    for h in range(len(closes) * 24 + 48):
        ts = start + pd.Timedelta(hours=h)
        btc_lines.append(
            f"{ts.isoformat()},{ts.isoformat()},50000,50010,49990,50000,100,5000000,1000"
        )
    btc_path = tmp_path / "btc_veto.csv"
    btc_path.write_text("\n".join(btc_lines), encoding="utf-8")
    return spy_path, btc_path


def test_drawdown_veto_flattens_open_position_in_simulator(tmp_path):
    """
    Drawdown veto in the replay simulator must close any open position
    (a SELL trade is appended) and block new entries.
    """
    from app.agents.brains.fake_brain import FakeBrain
    from app.domain.enums import Mode
    from app.simulator.replay_simulator import BarByBarSimulator

    # Build a price series that starts at 100, then drops sharply so that by
    # day 3 the drawdown (from peak equity) exceeds the 5% default limit.
    # Day 1: 100, Day 2: 100 (BUY entry at ~100), Day 3: 90 (drawdown ~10%)
    # Remaining days hold steady at 90 so the sim completes cleanly.
    closes = [100, 100, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90]
    spy_path, btc_path = _write_fixtures(tmp_path, closes)

    class _VetoSim(BarByBarSimulator):
        TEST_START = "2025-01-06"
        TEST_END = "2025-01-17"

    sim = _VetoSim(
        initial_capital=10000.0,
        spy_path=spy_path,
        btc_path=btc_path,
    )
    result = sim.run_simulation(
        target_market="US",
        mode=Mode.DEBATE,
        allow_short=False,
        max_dd=5.0,          # tight drawdown limit
        max_vol=99.0,        # disable vol veto
        brain=FakeBrain(Action.BUY),
    )

    # At least one trade must exist (the veto-forced close of the long position).
    # A closed long is recorded with side=BUY (the direction of the round-trip).
    closed_trades = [t for t in result.trades if t.exit]
    assert len(closed_trades) >= 1, (
        f"Expected at least one closed trade from drawdown veto flattening. "
        f"Trades: {result.trades}"
    )
    # The trade must be a loss (we bought at ~100, veto closed at ~90).
    forced_close = closed_trades[0]
    assert forced_close.pnl < 0, (
        f"Veto-forced close on falling price must be a loss. PnL={forced_close.pnl}"
    )


def test_cooloff_re_arms_after_configured_days(tmp_path):
    """
    After the drawdown veto fires and the cool-off period expires,
    normal BUY signals resume and a new BUY trade appears.
    Uses drawdown_cooloff_days=1 so only 1 extra day is blocked.
    """
    from app.agents.brains.fake_brain import FakeBrain
    from app.domain.enums import Mode
    from app.simulator.replay_simulator import BarByBarSimulator
    from app.risk.risk_layer import RiskLayer

    # 15 days: start at 100, drop to 90 on day 3 (triggers veto), stay at 90 for 1
    # cool-off day, then recover to 100 for the rest so a new BUY entry can happen.
    closes = [100, 100, 90, 90, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
    spy_path, btc_path = _write_fixtures(tmp_path, closes)

    class _CooloffSim(BarByBarSimulator):
        TEST_START = "2025-01-06"
        TEST_END = "2025-01-27"

        def run_simulation(self, *args, **kwargs):
            # Inject a RiskLayer with cooloff_days=1 for a fast test.
            from app.risk.risk_layer import RiskLayer as _RL
            orig = _RL.__init__

            def _patched_init(self_rl, **kw):
                kw.setdefault("stop_loss", 1.2)
                kw.setdefault("max_volatility", 99.0)
                kw.setdefault("max_drawdown", 5.0)
                kw["drawdown_cooloff_days"] = 1
                orig(self_rl, **kw)

            _RL.__init__ = _patched_init
            try:
                return super().run_simulation(*args, **kwargs)
            finally:
                _RL.__init__ = orig

    sim = _CooloffSim(
        initial_capital=10000.0,
        spy_path=spy_path,
        btc_path=btc_path,
    )
    result = sim.run_simulation(
        target_market="US",
        mode=Mode.DEBATE,
        allow_short=False,
        max_dd=5.0,
        max_vol=99.0,
        brain=FakeBrain(Action.BUY),
    )

    # The forced close of the first long is itself side=BUY, so one trade proves
    # nothing: re-arming requires a SECOND round trip.
    assert len(result.trades) >= 2, (
        f"Expected BUY re-entry after cool-off. Trades: {result.trades}"
    )


def test_breaker_re_arms_on_experiment_code_path(tmp_path):
    """Same call the validation experiment makes (run_simulation, no patching):
    after one breach and the cool-off, the position is re-entered and vetoes stop."""
    from app.agents.brains.fake_brain import FakeBrain
    from app.domain.enums import Mode
    from app.simulator.replay_simulator import BarByBarSimulator

    closes = [100, 100, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90]
    spy_path, btc_path = _write_fixtures(tmp_path, closes)

    class _Sim(BarByBarSimulator):
        TEST_START = "2025-01-06"
        TEST_END = "2025-01-22"

    result = _Sim(spy_path=spy_path, btc_path=btc_path).run_simulation(
        target_market="US", mode=Mode.DEBATE, max_vol=99.0,
        brain=FakeBrain(Action.BUY), drawdown_cooloff_days=2,
    )
    assert result.risk_veto_count == 3  # breach day + 2 cool-off days
    assert result.daily_decisions[-1].position_held == 1


def test_consensus_hold_keeps_open_position_in_simulator(tmp_path):
    """protocol.md section 10: BUY then HOLD stays long; no early round trip."""
    from app.agents.brains.fake_brain import FakeBrain
    from app.domain.enums import Mode
    from app.simulator.replay_simulator import BarByBarSimulator

    class _BuyThenHold(FakeBrain):
        def recommend(self, state, candles, knowledge):
            action = Action.BUY if candles[-1].close == 100 else Action.HOLD
            return action, 70.0, "scripted", []

    spy_path, btc_path = _write_fixtures(tmp_path, [100, 101, 101, 101, 101])

    class _Sim(BarByBarSimulator):
        TEST_START = "2025-01-06"
        TEST_END = "2025-01-10"

    result = _Sim(spy_path=spy_path, btc_path=btc_path).run_simulation(
        target_market="US", mode=Mode.SILENT_WEIGHTED, max_vol=99.0,
        brain=_BuyThenHold(Action.BUY),
    )
    assert [d.final_action for d in result.daily_decisions][1:] == [Action.HOLD] * 4
    assert [d.position_held for d in result.daily_decisions] == [1] * 5
    assert len(result.trades) == 1  # only the final bar close-out


@pytest.mark.parametrize("max_vol, max_dd, held_after", [(99.0, 5.0, 0), (2.0, 99.0, 1)])
def test_veto_on_open_position(tmp_path, max_vol, max_dd, held_after):
    """Option B: a drawdown breach flattens; a volatility override keeps the position."""
    from app.agents.brains.fake_brain import FakeBrain
    from app.domain.enums import Mode
    from app.simulator.replay_simulator import BarByBarSimulator

    spy_path, btc_path = _write_fixtures(tmp_path, [100, 100, 90, 90])

    class _Sim(BarByBarSimulator):
        TEST_START = "2025-01-06"
        TEST_END = "2025-01-09"

    result = _Sim(spy_path=spy_path, btc_path=btc_path).run_simulation(
        target_market="US", mode=Mode.SILENT_WEIGHTED, max_vol=max_vol, max_dd=max_dd,
        brain=FakeBrain(Action.BUY),
    )
    day3 = result.daily_decisions[2]
    assert day3.risk_status == RiskStatus.OVERRIDDEN
    assert day3.position_held == held_after
