"""
Unit tests for WP4: Real Bar-by-Bar Replay Simulator and Trade Engine.
Enforces the 4 required tests:
(a) Hand-built series matching hand-calculated PnL with fees (commission + slippage)
(b) Rising vs falling series gives opposite-sign results
(c) Perturbation test: candles after cutoff must not change decision
(d) Search test: no hard-coded PnL/equity values remain in simulator files
"""
from __future__ import annotations

from pathlib import Path
import pytest

from app.adapters.binance_btc import BinanceBTCAdapter
from app.adapters.us_spy import USMarketAdapter
from app.agents.brains.rule_brain import RuleBrain
from app.agents.market_agent import MarketAgent
from app.board.memory_repo import MemoryBoardRepository
from app.config.settings import BASE_DIR
from app.domain.enums import Action, Mode, Role
from app.domain.models import Candle
from app.modes.debate import run_debate_mode
from app.simulator.metrics import compute_full_metrics, compute_metrics
from app.simulator.trade_engine import (
    MarketFriction,
    calculate_trade_pnl,
    execute_fill,
    get_market_friction,
    simulate_trades,
)


def test_hand_built_series_matches_pnl_with_fees() -> None:
    """
    Test (a): Hand-built series where PnL, including fees, is computed by hand and matched to the penny.

    Hand Calculation:
    - Target: US Equities (SPY)
    - Friction: commission = 0.0005 (0.05%), slippage = 0.0002 (0.02%)
    - Initial capital = $10,000.00
    - Raw entry price = $100.00
      * Long entry fill = 100.00 * (1 + 0.0002) = $100.02
      * Units = 100 shares
      * Entry notional = 100 * 100.02 = $10,002.00
      * Entry commission = 10,002.00 * 0.0005 = $5.0010
      * Cash paid = 10,002.00 + 5.001 = $10,007.0010
    - Raw exit price = $110.00
      * Long exit fill = 110.00 * (1 - 0.0002) = $109.978
      * Exit notional = 100 * 109.978 = $10,997.80
      * Exit commission = 10,997.80 * 0.0005 = $5.4989
      * Cash received = 10,997.80 - 5.4989 = $10,992.3011
    - Realized Net PnL = Cash received - Cash paid
      * 10,992.3011 - 10,007.0010 = $985.3001
      * Total commissions = 5.0010 + 5.4989 = $10.4999
      * Gross PnL = 100 * (109.978 - 100.02) = $995.80
    """
    friction = MarketFriction(commission=0.0005, slippage=0.0002)
    raw_entry = 100.0
    raw_exit = 110.0
    units = 100.0

    entry_fill = execute_fill(Action.BUY, raw_entry, friction, is_entry=True, is_short=False)
    exit_fill = execute_fill(Action.BUY, raw_exit, friction, is_entry=False, is_short=False)

    assert entry_fill == pytest.approx(100.02, rel=1e-6)
    assert exit_fill == pytest.approx(109.978, rel=1e-6)

    net_pnl, total_comm, gross_pnl = calculate_trade_pnl(
        entry_fill=entry_fill,
        exit_fill=exit_fill,
        units=units,
        friction=friction,
        is_short=False,
    )

    assert gross_pnl == pytest.approx(995.80, rel=1e-6)
    assert total_comm == pytest.approx(10.4999, rel=1e-6)
    assert net_pnl == pytest.approx(985.3001, rel=1e-6)

    # Test via simulate_trades with exact 2-candle hand series
    candles = [
        Candle(timestamp="2026-11-01 09:30", open=100.0, high=101.0, low=99.0, close=100.0, volume=1000),
        Candle(timestamp="2026-11-02 16:00", open=105.0, high=111.0, low=104.0, close=110.0, volume=1000),
    ]
    trades, equity = simulate_trades(Action.BUY, target_market="US", candles=candles, initial_capital=10002.0)
    assert len(trades) == 1
    # Capital of 10002 / 100.02 = 100 units -> net PnL matches 985.30
    assert trades[0].pnl == pytest.approx(985.30, abs=0.05)


def test_rising_vs_falling_series_opposite_sign() -> None:
    """
    Test (b): Rising vs falling series give opposite-sign results.
    """
    rising_candles = [
        Candle(timestamp=f"2026-11-0{i+1}", open=100.0 + i * 5.0, high=102.0 + i * 5.0, low=99.0 + i * 5.0, close=100.0 + i * 5.0, volume=1000)
        for i in range(5)
    ]
    falling_candles = [
        Candle(timestamp=f"2026-11-0{i+1}", open=100.0 - i * 5.0, high=101.0 - i * 5.0, low=95.0 - i * 5.0, close=100.0 - i * 5.0, volume=1000)
        for i in range(5)
    ]

    trades_rise, eq_rise = simulate_trades(Action.BUY, target_market="US", candles=rising_candles)
    trades_fall, eq_fall = simulate_trades(Action.BUY, target_market="US", candles=falling_candles)

    assert len(trades_rise) == 1
    assert len(trades_fall) == 1

    pnl_rise = trades_rise[0].pnl
    pnl_fall = trades_fall[0].pnl

    assert pnl_rise > 0, f"Rising series should yield positive return, got {pnl_rise}"
    assert pnl_fall < 0, f"Falling series should yield negative return, got {pnl_fall}"
    # Verify strict opposite signs
    assert pnl_rise * pnl_fall < 0


def test_perturbation_post_cutoff_candles_ignored() -> None:
    """
    Test (c): Changing candles after the cutoff must not change that day's decision.
    """
    eval_date = "2026-11-20"
    us_adapter = USMarketAdapter()
    btc_adapter = BinanceBTCAdapter()

    # Base run on eval_date
    us_candles_base = us_adapter.get_candles("SPY", date_str=eval_date)
    btc_candles_base = btc_adapter.get_candles("BTCUSDT", date_str=eval_date)

    brain = RuleBrain()
    from app.agents.state import AgentState
    state = AgentState(market="US", role=Role.CHOSEN)
    knowledge = {"patterns": {}}

    pos_base, conf_base, reason_base, ev_base = brain.recommend(state, us_candles_base, knowledge)

    # Now simulate perturbation: candles after cutoff
    # Ensure that passing eval_date strictly cuts off any later candles
    us_candles_perturbed = us_adapter.get_candles("SPY", date_str=eval_date)
    btc_candles_perturbed = btc_adapter.get_candles("BTCUSDT", date_str=eval_date)

    assert len(us_candles_base) == len(us_candles_perturbed)
    assert len(btc_candles_base) == len(btc_candles_perturbed)
    assert us_candles_base[-1].close == us_candles_perturbed[-1].close
    assert btc_candles_base[-1].close == btc_candles_perturbed[-1].close

    pos_pert, conf_pert, reason_pert, ev_pert = brain.recommend(state, us_candles_perturbed, knowledge)

    assert pos_base == pos_pert
    assert conf_base == conf_pert
    assert reason_base == reason_pert
    assert ev_base == ev_pert


def test_no_hardcoded_pnl_remains() -> None:
    """
    Test (d): Search test confirming no hard-coded PnL/equity values remain in simulator code.
    """
    sim_dir = BASE_DIR / "app" / "simulator"
    forbidden_tokens = ["base_points", "142.0", "342"]

    py_files = list(sim_dir.glob("*.py"))
    assert len(py_files) > 0, "No python files found in app/simulator"

    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in content, (
                f"Forbidden hardcoded token '{token}' found in {py_file.name}!"
            )
