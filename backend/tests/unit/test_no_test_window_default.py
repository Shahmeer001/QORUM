"""Replay scripts other than run_final_test.py must not open the held-out window."""
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import run_wp4_experiment
from app.simulator.replay_simulator import BarByBarSimulator


class _Stop(Exception):
    pass


def test_wp4_experiment_stays_before_the_test_window(monkeypatch):
    seen = []

    def spy(self, *args, **kwargs):
        seen.append((self.TEST_START, self.TEST_END))
        raise _Stop  # stop before any data is loaded

    monkeypatch.setattr(BarByBarSimulator, "__init__", spy)
    with pytest.raises(_Stop):
        run_wp4_experiment.run_experiments()
    assert seen == [("2024-01-01", "2024-12-31")]


def test_no_script_builds_the_default_window_simulator():
    offenders = [p.name for p in SCRIPTS.glob("*.py")
                 if "BarByBarSimulator()" in p.read_text(encoding="utf-8")]
    assert offenders == []
