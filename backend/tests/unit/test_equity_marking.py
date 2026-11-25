"""
Daily equity must reflect only fills that have happened by that day's close.
US orders decided on day i fill at day i+1's OPEN, so day i's equity is marked
with the position held before that fill.
"""
import pytest

from app.agents.brains.fake_brain import FakeBrain
from app.domain.enums import Action, Mode
from app.domain.models import EquityPoint
from app.simulator.metrics import compute_full_metrics
from app.simulator.replay_simulator import BarByBarSimulator
from app.simulator.trade_engine import get_market_friction
from tests.unit.test_risk_veto_semantics import _write_fixtures

OPENS = [100.0, 104.0, 115.0, 125.0]
CLOSES = [100.0, 110.0, 120.0, 130.0]
DATES = ["06/01/2025", "07/01/2025", "08/01/2025", "09/01/2025"]


class _Sim(BarByBarSimulator):
    TEST_START = "2025-01-06"
    TEST_END = "2025-01-09"


def test_us_equity_per_day_matches_hand_calculation(tmp_path):
    spy_path, btc_path = _write_fixtures(tmp_path, CLOSES)
    spy_path.write_text("\n".join(
        ["Date,Open,High,Low,Close,Volume"]
        + [f"{d} 16:00:00,{o},{c + 1},{o - 1},{c},1000000" for d, o, c in zip(DATES, OPENS, CLOSES)]
    ), encoding="utf-8")

    result = _Sim(initial_capital=10000.0, spy_path=spy_path, btc_path=btc_path).run_simulation(
        "US", Mode.SILENT_WEIGHTED, max_vol=99.0, max_dd=99.0, brain=FakeBrain(Action.BUY),
    )

    f = get_market_friction("US")
    fill = 104.0 * (1 + f.slippage)          # day-0 BUY fills at day-1 open
    units = 10000.0 / fill
    cash = -10000.0 * f.commission
    exit_notional = units * 130.0 * (1 - f.slippage)
    expected = [
        10000.0,                             # day 0: not filled yet
        cash + units * 110.0,
        cash + units * 120.0,
        cash + exit_notional * (1 - f.commission),  # final close-out
    ]
    assert [p.v for p in result.equity_curve] == pytest.approx(expected, abs=0.01)
    assert result.pnl_pct == pytest.approx((expected[-1] / 10000.0 - 1) * 100, abs=0.01)
    assert result.exposure_pct == 75.0       # exposed at 3 of 4 closes
    # Buy-and-hold pays the same costs, so it equals an always-BUY strategy.
    assert result.benchmark_buy_hold_return_pct == pytest.approx(result.pnl_pct, abs=0.01)


def test_return_is_measured_from_initial_capital():
    """A first equity point that already paid entry costs must not hide them."""
    curve = [EquityPoint(t="a", v=9990.0), EquityPoint(t="b", v=10989.0)]
    assert compute_full_metrics([], curve, 2, 2, 0.0, 10000.0).pnl_pct == 9.89
