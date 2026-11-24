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


def test_weight_on_day_t_does_not_depend_on_day_t_outcome(tmp_path):
    """
    No look-ahead: the accuracy weight used on day t must not depend on what
    happens on day t.  To verify this, we run two SmallSims on CSVs that are
    identical through day 2 but differ only on day 3's close (±5%).  The
    accuracy snapshots after day 2 (i.e. the weights that govern day-3 decisions)
    must be identical in both runs.
    """
    dates_6 = [
        "2025-01-06", "2025-01-07", "2025-01-08",
        "2025-01-09", "2025-01-10", "2025-01-13",
    ]

    def _write_csv(base, closes):
        spy_lines = ["Date,Open,High,Low,Close,Volume"]
        for d, c in zip(dates_6, closes):
            dd = f"{d[8:10]}/{d[5:7]}/{d[:4]}"
            spy_lines.append(f"{dd} 16:00:00,{c},{c+1},{c-1},{c},1000000")
        spy_path = base / "spy.csv"
        spy_path.write_text("\n".join(spy_lines), encoding="utf-8")

        btc_lines = ["timestamp,Date,Open,High,Low,Close,Volume,QuoteVolume,Trades"]
        start = pd.Timestamp("2025-01-06 00:00:00+00:00")
        for h in range(192):
            ts = start + pd.Timedelta(hours=h)
            btc_lines.append(
                f"{ts.isoformat()},{ts.isoformat()},50000,50010,49990,50000,100,5000000,1000"
            )
        btc_path = base / "btc.csv"
        btc_path.write_text("\n".join(btc_lines), encoding="utf-8")
        return spy_path, btc_path

    # Base closes: 100, 101, 102, 103, 104, 105 (rising)
    base_closes = [100, 101, 102, 103, 104, 105]
    # Perturbed: same through day 2 (index 0-1), day 3 (index 2) is +5%
    perturbed_closes = [100, 101, 107, 103, 104, 105]  # day 3 close perturbed

    path_a = tmp_path / "a"
    path_a.mkdir()
    path_b = tmp_path / "b"
    path_b.mkdir()

    spy_a, btc_a = _write_csv(path_a, base_closes)
    spy_b, btc_b = _write_csv(path_b, perturbed_closes)

    sim_a = _SmallSim(initial_capital=10000.0, spy_path=spy_a, btc_path=btc_a)
    sim_b = _SmallSim(initial_capital=10000.0, spy_path=spy_b, btc_path=btc_b)

    res_a = sim_a.run_simulation(
        target_market="US", mode=Mode.DEBATE, allow_short=False, brain=FakeBrain(Action.BUY)
    )
    res_b = sim_b.run_simulation(
        target_market="US", mode=Mode.DEBATE, allow_short=False, brain=FakeBrain(Action.BUY)
    )

    # The final_accuracy at the end of a 6-day run includes scores from days 1-5.
    # We want to compare the state after days 1-2 only. Because the simulator
    # applies accuracy updates at the START of each day (scoring the previous day),
    # the state entering day 3 equals the state after scoring day 2.
    # We verify this by running a 3-day sub-window (days 1-3).

    class _Day3Sim(BarByBarSimulator):
        TEST_START = "2025-01-06"
        TEST_END = "2025-01-08"  # 3 evaluation days: 1/6, 1/7, 1/8

    sim_c = _Day3Sim(initial_capital=10000.0, spy_path=spy_a, btc_path=btc_a)
    sim_d = _Day3Sim(initial_capital=10000.0, spy_path=spy_b, btc_path=btc_b)

    res_c = sim_c.run_simulation(
        target_market="US", mode=Mode.DEBATE, allow_short=False, brain=FakeBrain(Action.BUY)
    )
    res_d = sim_d.run_simulation(
        target_market="US", mode=Mode.DEBATE, allow_short=False, brain=FakeBrain(Action.BUY)
    )

    # After day 3, the accuracy update applied was: score(day 2's call vs day 3 close).
    # day 2's call (BUY) is correct iff close[day3] > close[day2].
    # In both CSVs, close[day2]=101. In A, close[day3]=102 (correct); in B, close[day3]=107 (also correct).
    # So the direction is the same, meaning the accuracy after day 3 should be the same.
    # To test purely day-1-to-day-2 accuracy (independent of day 3):
    # run a 2-day sub-window that excludes day 3 entirely.

    class _Day2Sim(BarByBarSimulator):
        TEST_START = "2025-01-06"
        TEST_END = "2025-01-07"  # 2 evaluation days: 1/6, 1/7

    sim_e = _Day2Sim(initial_capital=10000.0, spy_path=spy_a, btc_path=btc_a)
    sim_f = _Day2Sim(initial_capital=10000.0, spy_path=spy_b, btc_path=btc_b)

    res_e = sim_e.run_simulation(
        target_market="US", mode=Mode.DEBATE, allow_short=False, brain=FakeBrain(Action.BUY)
    )
    res_f = sim_f.run_simulation(
        target_market="US", mode=Mode.DEBATE, allow_short=False, brain=FakeBrain(Action.BUY)
    )

    # Both runs use the same data for days 1-2; the accuracy after day 2 must be equal.
    assert res_e.final_accuracy == res_f.final_accuracy, (
        f"Accuracy after days 1-2 must not depend on day-3 data.\n"
        f"Run A (base):       {res_e.final_accuracy}\n"
        f"Run B (perturbed):  {res_f.final_accuracy}"
    )
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
