"""
Tests for Part 0.1 (accuracy learning) and the bookkeeping definitions.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.agents.brains.fake_brain import FakeBrain
from app.domain.enums import Action, DataStatus, Mode
from app.simulator.replay_simulator import BarByBarSimulator
from app.supervisor import live_accuracy
from app.supervisor.accuracy import AccuracyTracker
from app.supervisor.accuracy_bookkeeper import (
    apply_outcome,
    is_correct,
    position_sign,
    realised_sign,
)

SPY_DATES = [
    "2025-01-06", "2025-01-07", "2025-01-08",
    "2025-01-09", "2025-01-10", "2025-01-13",
]


def _write_fixtures(base: Path, rising: bool):
    closes = [100 + i for i in range(6)] if rising else [105 - i for i in range(6)]
    spy_lines = ["Date,Open,High,Low,Close,Volume"]
    for d, c in zip(SPY_DATES, closes):
        dd = f"{d[8:10]}/{d[5:7]}/{d[:4]}"  # DD/MM/YYYY
        spy_lines.append(f"{dd} 16:00:00,{c},{c + 1},{c - 1},{c},1000000")
    spy_path = base / "spy_small.csv"
    spy_path.write_text("\n".join(spy_lines), encoding="utf-8")

    btc_lines = ["timestamp,Date,Open,High,Low,Close,Volume,QuoteVolume,Trades"]
    start = pd.Timestamp("2025-01-06 00:00:00+00:00")
    for h in range(192):  # 8 days of hourly bars covers the window
        ts = start + pd.Timedelta(hours=h)
        btc_lines.append(
            f"{ts.isoformat()},{ts.isoformat()},50000,50010,49990,50000,100,5000000,1000"
        )
    btc_path = base / "btc_small.csv"
    btc_path.write_text("\n".join(btc_lines), encoding="utf-8")
    return spy_path, btc_path


class _SmallSim(BarByBarSimulator):
    TEST_START = "2025-01-06"
    TEST_END = "2025-01-13"


def test_neutral_priors_loaded_for_all_markets():
    t = AccuracyTracker()
    for m in ["US", "CRYPTO", "PSX", "FOREX", "GOLD"]:
        assert t.get_accuracy(m) == 0.5


def test_bookkeeper_correctness_definitions():
    assert position_sign(Action.BUY) == 1
    assert position_sign(Action.SELL) == -1
    assert position_sign(Action.HOLD) == 0
    assert realised_sign(0.01) == 1
    assert realised_sign(-0.01) == -1
    assert realised_sign(0.0) == 0

    assert is_correct(Action.BUY, 0.01) is True
    assert is_correct(Action.BUY, -0.01) is False
    assert is_correct(Action.SELL, -0.01) is True
    assert is_correct(Action.SELL, 0.01) is False
    # HOLD is correct only on an exactly flat holding period.
    assert is_correct(Action.HOLD, 0.0) is True
    assert is_correct(Action.HOLD, 0.01) is False


def test_apply_outcome_updates_and_excludes_abstain_and_missing_data():
    t = AccuracyTracker()
    start = t.get_accuracy("US")
    finals = {
        "US": (Action.BUY, DataStatus.VALID),
        "CRYPTO": (Action.ABSTAIN, DataStatus.VALID),
        "PSX": (Action.BUY, DataStatus.NO_DATA),
    }
    apply_outcome(t, finals, 0.02)  # positive realised return
    assert t.get_accuracy("US") > start          # BUY correct -> rises
    assert t.get_accuracy("CRYPTO") == start     # ABSTAIN excluded
    assert t.get_accuracy("PSX") == start        # NO_DATA excluded


def test_weights_diverge_in_replay_on_rising_market(tmp_path):
    """Correct BUY calls on a rising market push accuracy above the neutral prior."""
    spy_path, btc_path = _write_fixtures(tmp_path, rising=True)
    sim = _SmallSim(initial_capital=10000.0, spy_path=spy_path, btc_path=btc_path)
    res = sim.run_simulation(
        target_market="US", mode=Mode.DEBATE, allow_short=False, brain=FakeBrain(Action.BUY)
    )
    assert res.final_accuracy["US"] > 0.5, res.final_accuracy
    assert res.final_accuracy["CRYPTO"] > 0.5  # CRYPTO also BUY-correct on rising US


def test_weights_diverge_in_replay_on_falling_market(tmp_path):
    """Wrong BUY calls on a falling market pull accuracy below the neutral prior."""
    spy_path, btc_path = _write_fixtures(tmp_path, rising=False)
    sim = _SmallSim(initial_capital=10000.0, spy_path=spy_path, btc_path=btc_path)
    res = sim.run_simulation(
        target_market="US", mode=Mode.DEBATE, allow_short=False, brain=FakeBrain(Action.BUY)
    )
    assert res.final_accuracy["US"] < 0.5, res.final_accuracy


def test_live_accuracy_carries_state_across_sessions():
    live_accuracy.reset()
    t = live_accuracy.get_tracker("US")
    assert t.get_accuracy("US") == 0.5
    apply_outcome(t, {"US": (Action.BUY, DataStatus.VALID)}, 0.02)
    assert t.get_accuracy("US") > 0.5
    live_accuracy.set_last("US", "2026-11-19", 100.0, {"US": (Action.BUY, DataStatus.VALID)})
    last = live_accuracy.get_last("US")
    assert last is not None and last["close"] == 100.0
    assert live_accuracy.get_tracker("US") is t  # same tracker persists across calls
    live_accuracy.reset()
