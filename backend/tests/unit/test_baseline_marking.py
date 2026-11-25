"""
Hand-built check of the two baseline scripts: a BUY decided on day 0 fills at the
day-1 open (104), so day 0 is flat and return is measured from initial capital.
"""
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import run_baselines
import run_rule_baselines
from app.domain.enums import Action
from app.simulator.trade_engine import get_market_friction

DAYS = [date(2024, 1, d) for d in (2, 3, 4, 5)]
OPENS = [100.0, 104.0, 115.0, 125.0]
CLOSES = [100.0, 110.0, 120.0, 130.0]


def _expected_return_pct():
    f = get_market_friction("US")
    units = 10000.0 / (104.0 * (1 + f.slippage))
    exit_notional = units * 130.0 * (1 - f.slippage)
    final = -10000.0 * f.commission + exit_notional * (1 - f.commission)
    return (final / 10000.0 - 1) * 100


def test_rule_baseline_engine():
    pnl, max_dd, *_ = run_rule_baselines._simulate_from_signals(
        "US", DAYS, {d: "BUY" for d in DAYS}, {}, None,
        exec_raw_map=dict(zip(DAYS, OPENS[1:] + CLOSES[-1:])),
        curr_close_map=dict(zip(DAYS, CLOSES)),
    )
    assert pnl == pytest.approx(_expected_return_pct(), abs=0.01)
    assert max_dd == 0.0  # nothing is lost before the fill


def test_random_trader_engine(monkeypatch):
    monkeypatch.setattr(run_baselines.random.Random, "choice", lambda self, pool: Action.BUY)

    class _Sim:
        evaluation_days = DAYS
        spy_df = pd.DataFrame({"parsed_date": DAYS, "Open": OPENS, "Close": CLOSES})

    res = run_baselines.run_random_trader(_Sim(), "US", n_seeds=1)
    assert res["mean_return_pct"] == pytest.approx(_expected_return_pct(), abs=0.01)
    assert res["mean_max_dd_pct"] == 0.0
