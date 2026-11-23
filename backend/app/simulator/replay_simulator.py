"""
Historical Bar-by-Bar Replay Simulator.
Runs multi-day cross-market agent evaluation strictly respecting temporal boundaries.

Rules Enforced:
1. Learning window: 2022-01-03 to 2024-12-31 (knowledge base built strictly from this window).
2. Test window: 2025-01-01 to 2026-11-20 (held out strictly for out-of-sample evaluation; no tuning).
3. Evaluation days: US trading days where BOTH active markets (US/SPY and CRYPTO/BTC) have valid candles.
4. Degraded days: Days where one market is closed (e.g. US market holidays/weekends where SPY has no candle).
   Degraded days are strictly excluded from main evaluation metrics, counted, and reported separately.
5. Two sessions per day: target=US (CRYPTO informs) and target=CRYPTO (US informs).
   Reported separately, never averaged.
6. Execution & Fills:
   - Signals use only candles closed at or before the cutoff (16:00 ET / 21:00 UTC).
   - SPY fills at the NEXT US trading day's open.
   - BTC fills at the open of the first 1h candle starting at the cutoff (21:00 UTC).
   - A position is held until the next decision.
   - Per-market friction: US (0.05% comm, 0.02% slip); CRYPTO (0.10% comm, 0.05% slip).
   - Long/flat by default; shorting evaluated behind allow_short.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd

from app.adapters.binance_btc import BinanceBTCAdapter
from app.adapters.us_spy import USMarketAdapter
from app.agents.market_agent import MarketAgent
from app.board.memory_repo import MemoryBoardRepository
from app.config.settings import DATA_CACHE_DIR, INITIAL_CAPITAL, get_us_close_utc
from app.domain.enums import Action, Mode, RiskStatus, Role
from app.domain.models import Candle, EquityPoint, Trade
from app.modes.debate import run_debate_mode
from app.modes.silent import run_silent_mode
from app.modes.single import run_single_mode
from app.risk.risk_layer import RiskLayer
from app.simulator.metrics import PerformanceSummary, compute_full_metrics
from app.simulator.trade_engine import (
    MarketFriction,
    calculate_trade_pnl,
    execute_fill,
    get_market_friction,
)


@dataclass
class DailyDecisionRecord:
    date: str
    target: str
    mode: Mode
    consensus: Action
    final_action: Action
    risk_status: RiskStatus
    reason: str
    fill_price: Optional[float] = None
    position_held: int = 0  # +1 long, -1 short, 0 flat


@dataclass
class SimulationResult:
    target_market: str
    mode: Mode
    allow_short: bool
    initial_capital: float
    final_equity: float
    pnl_dollars: float
    pnl_pct: float
    max_drawdown_pct: float
    hit_rate_pct: float
    exposure_pct: float
    exposure_adjusted_return_pct: float
    sharpe_ratio: float
    trade_count: int
    turnover: float
    evaluation_days_count: int
    degraded_days_count: int
    trades: List[Trade]
    equity_curve: List[EquityPoint]
    daily_decisions: List[DailyDecisionRecord]
    degraded_days: List[Dict[str, str]]


class BarByBarSimulator:
    """
    Deterministic historical backtest simulator.
    Evaluates agents on the test window (2025-01-01 to 2026-11-20).
    """

    LEARNING_START = "2022-01-03"
    LEARNING_END = "2024-12-31"
    TEST_START = "2025-01-01"
    TEST_END = "2026-11-20"

    def __init__(
        self,
        initial_capital: float = INITIAL_CAPITAL,
        spy_path: Optional[Path] = None,
        btc_path: Optional[Path] = None,
    ) -> None:
        self.initial_capital = initial_capital
        self.spy_path = spy_path or (DATA_CACHE_DIR / "spy_daily.csv")
        self.btc_path = btc_path or (DATA_CACHE_DIR / "btc_1h.csv")

        # Load datasets
        self._load_datasets()
        # Classify evaluation vs degraded days
        self.evaluation_days: List[date] = []
        self.degraded_days: List[Dict[str, str]] = []
        self._classify_days()

    def _load_datasets(self) -> None:
        # Load SPY
        spy_df = pd.read_csv(self.spy_path)
        spy_df["parsed_date"] = pd.to_datetime(
            spy_df["Date"].astype(str).str.split().str[0], format="%d/%m/%Y"
        ).dt.date
        spy_df = spy_df.sort_values("parsed_date").reset_index(drop=True)
        self.spy_df = spy_df
        self.spy_trading_dates: Set[date] = set(spy_df["parsed_date"])

        # Load BTC
        btc_df = pd.read_csv(self.btc_path)
        btc_df["open_dt"] = pd.to_datetime(btc_df["timestamp"])
        btc_df["close_dt"] = btc_df["open_dt"] + pd.Timedelta(hours=1)
        btc_df = btc_df.sort_values("open_dt").reset_index(drop=True)
        self.btc_df = btc_df

    def _classify_days(self) -> None:
        """
        Classifies calendar days in the test window (2025-01-01 to 2026-11-20):
        - Evaluation days: US trading days where BOTH SPY and BTC have valid candles.
        - Degraded days: Days where one or both lack valid data (e.g. US market holidays).
        """
        start_d = pd.to_datetime(self.TEST_START).date()
        end_d = pd.to_datetime(self.TEST_END).date()
        curr = start_d

        while curr <= end_d:
            d_str = curr.isoformat()
            is_spy_open = curr in self.spy_trading_dates

            # Check BTC availability at cutoff
            cutoff = get_us_close_utc(d_str)
            btc_candles = self.btc_df[self.btc_df["close_dt"] <= cutoff]
            has_btc = len(btc_candles) > 0 and (cutoff - btc_candles["close_dt"].max()).total_seconds() <= 3600

            if is_spy_open and has_btc:
                self.evaluation_days.append(curr)
            else:
                reason = []
                if not is_spy_open:
                    reason.append("US market closed (weekend / NYSE holiday)")
                if not has_btc:
                    reason.append("BTC data unavailable at cutoff")
                self.degraded_days.append({
                    "date": d_str,
                    "reason": "; ".join(reason),
                })

            curr += timedelta(days=1)

    def run_simulation(
        self,
        target_market: str,
        mode: Mode = Mode.DEBATE,
        allow_short: bool = False,
        stop_loss: float = 1.2,
        max_vol: float = 2.5,
        max_dd: float = 5.0,
        min_margin: float = 0.0,
    ) -> SimulationResult:
        """
        Executes bar-by-bar simulation for the chosen target market across all evaluation days.
        Reports strictly for target_market.
        """
        target = target_market.upper()
        friction = get_market_friction(target)
        symbol = "SPY" if target == "US" else "BTCUSDT"

        us_adapter = USMarketAdapter(csv_path=self.spy_path)
        btc_adapter = BinanceBTCAdapter(csv_path=self.btc_path)
        risk_layer = RiskLayer(stop_loss=stop_loss, max_volatility=max_vol, max_drawdown=max_dd)

        cash = self.initial_capital
        current_pos = 0  # +1 long, -1 short, 0 flat
        units = 0.0
        entry_fill_price = 0.0
        entry_comm_paid = 0.0
        entry_time_str = ""

        trades: List[Trade] = []
        equity_curve: List[EquityPoint] = []
        daily_decisions: List[DailyDecisionRecord] = []

        total_volume_traded = 0.0
        days_exposed = 0

        # Pre-index SPY rows by date for O(1) lookups
        spy_by_date = {row["parsed_date"]: row for _, row in self.spy_df.iterrows()}
        all_eval_days = self.evaluation_days
        n_days = len(all_eval_days)

        for i, eval_date in enumerate(all_eval_days):
            d_str = eval_date.isoformat()

            # 1. Temporal boundary: date_str locks adapters to candles closed <= cutoff on eval_date
            us_adapter.current_date = d_str
            btc_adapter.current_date = d_str

            # 2. Setup board & agents with appropriate roles
            board = MemoryBoardRepository()
            agents: Dict[str, MarketAgent] = {
                "US": MarketAgent(
                    market="US",
                    adapter=us_adapter,
                    board=board,
                    role=Role.CHOSEN if target == "US" else Role.RELATED,
                ),
                "CRYPTO": MarketAgent(
                    market="CRYPTO",
                    adapter=btc_adapter,
                    board=board,
                    role=Role.CHOSEN if target == "CRYPTO" else Role.RELATED,
                ),
            }

            session_id = f"sim_{target}_{d_str}"

            # 3. Deliberation according to mode
            if mode == Mode.SINGLE:
                _, consensus, _, _ = run_single_mode(
                    agents=agents,
                    board=board,
                    session_id=session_id,
                    target_market=target,
                    asset=symbol,
                )
            elif mode == Mode.SILENT:
                _, consensus, _, _ = run_silent_mode(
                    agents=agents,
                    board=board,
                    session_id=session_id,
                    asset=symbol,
                    min_margin=min_margin,
                )
            else:  # Mode.DEBATE
                _, consensus, _, _ = run_debate_mode(
                    agents=agents,
                    board=board,
                    session_id=session_id,
                    asset=symbol,
                    max_turns=3,
                    min_margin=min_margin,
                )

            # 4. Target candles closed <= cutoff for Risk Governance
            target_adapter = us_adapter if target == "US" else btc_adapter
            closed_candles = target_adapter.get_candles(symbol=symbol, limit=100)

            final_action, risk_status, risk_note, _ = risk_layer.evaluate(
                consensus=consensus,
                candles=closed_candles,
            )

            # 5. Determine target position stance
            if final_action == Action.BUY:
                target_pos = 1
            elif final_action == Action.SELL:
                target_pos = -1 if allow_short else 0
            else:  # HOLD or ABSTAIN
                target_pos = 0

            # 6. Execution Fills:
            # - SPY: fills at NEXT US trading day's open
            # - BTC: fills at open of first 1h candle starting at cutoff (21:00 UTC)
            fill_price_for_record = None

            if target == "US":
                # Next US trading day
                if i + 1 < n_days:
                    next_date = all_eval_days[i + 1]
                    next_row = spy_by_date.get(next_date)
                    exec_raw_price = float(next_row["Open"]) if next_row is not None else float(closed_candles[-1].close)
                    exec_time_str = f"{next_date.isoformat()} 09:30:00-05:00"
                    current_close_price = float(closed_candles[-1].close)
                else:
                    exec_raw_price = float(closed_candles[-1].close)
                    exec_time_str = f"{d_str} 16:00:00-05:00"
                    current_close_price = float(closed_candles[-1].close)
            else:  # CRYPTO (BTC)
                # First 1h candle starting at cutoff (e.g. 21:00:00 UTC)
                cutoff = get_us_close_utc(d_str)
                # Next candle starting at cutoff
                next_candle = self.btc_df[self.btc_df["open_dt"] >= cutoff].head(1)
                if len(next_candle) > 0:
                    exec_raw_price = float(next_candle.iloc[0]["Open"])
                    exec_time_str = next_candle.iloc[0]["open_dt"].strftime("%Y-%m-%d %H:%M:%S+00:00")
                else:
                    exec_raw_price = float(closed_candles[-1].close)
                    exec_time_str = f"{d_str} 21:00:00+00:00"
                current_close_price = float(closed_candles[-1].close)

            # 7. Position change & Trade Execution
            if target_pos != current_pos:
                # Close existing position if any
                if current_pos != 0:
                    exit_fill = execute_fill(
                        action=Action.SELL if current_pos == 1 else Action.BUY,
                        raw_price=exec_raw_price,
                        friction=friction,
                        is_entry=False,
                        is_short=(current_pos == -1),
                    )
                    net_pnl, total_comm, gross = calculate_trade_pnl(
                        entry_fill=entry_fill_price,
                        exit_fill=exit_fill,
                        units=units,
                        friction=friction,
                        is_short=(current_pos == -1),
                    )
                    exit_notional = units * exit_fill
                    total_volume_traded += exit_notional

                    if current_pos == 1:
                        cash += exit_notional - (exit_notional * friction.commission)
                    else:  # Short cover
                        cash += gross - (exit_notional * friction.commission)

                    trades.append(
                        Trade(
                            entry=entry_time_str,
                            exit=exec_time_str,
                            side=Action.BUY if current_pos == 1 else Action.SELL,
                            market=target,
                            pnl=round(net_pnl, 2),
                            note=(
                                f"Exit {'Long' if current_pos == 1 else 'Short'} at {exit_fill:.2f} "
                                f"(gross: ${gross:.2f}, comm: ${total_comm:.2f})"
                            ),
                        )
                    )
                    current_pos = 0
                    units = 0.0

                # Open new position if target_pos is non-zero
                if target_pos != 0:
                    entry_fill = execute_fill(
                        action=Action.BUY if target_pos == 1 else Action.SELL,
                        raw_price=exec_raw_price,
                        friction=friction,
                        is_entry=True,
                        is_short=(target_pos == -1),
                    )
                    fill_price_for_record = entry_fill
                    entry_fill_price = entry_fill
                    entry_time_str = exec_time_str

                    # Sizing: deploy available cash (long) or initial capital (short)
                    capital_to_deploy = cash if target_pos == 1 else self.initial_capital
                    units = capital_to_deploy / entry_fill if entry_fill > 0 else 0.0
                    entry_notional = units * entry_fill
                    entry_comm = entry_notional * friction.commission
                    total_volume_traded += entry_notional
                    entry_comm_paid = entry_comm

                    if target_pos == 1:
                        cash -= (entry_notional + entry_comm)
                    else:
                        cash -= entry_comm

                    current_pos = target_pos

            # 8. Mark-to-market daily equity tracking
            if current_pos == 1:
                daily_equity = cash + units * current_close_price
                days_exposed += 1
            elif current_pos == -1:
                daily_equity = cash + self.initial_capital + units * (entry_fill_price - current_close_price)
                days_exposed += 1
            else:
                daily_equity = cash

            equity_curve.append(
                EquityPoint(
                    t=d_str,
                    v=round(daily_equity, 2),
                )
            )

            daily_decisions.append(
                DailyDecisionRecord(
                    date=d_str,
                    target=target,
                    mode=mode,
                    consensus=consensus,
                    final_action=final_action,
                    risk_status=risk_status,
                    reason=risk_note,
                    fill_price=fill_price_for_record,
                    position_held=current_pos,
                )
            )

        # 9. Close any remaining open position at final price
        if current_pos != 0:
            final_raw = float(closed_candles[-1].close)
            exit_fill = execute_fill(
                action=Action.SELL if current_pos == 1 else Action.BUY,
                raw_price=final_raw,
                friction=friction,
                is_entry=False,
                is_short=(current_pos == -1),
            )
            net_pnl, total_comm, gross = calculate_trade_pnl(
                entry_fill=entry_fill_price,
                exit_fill=exit_fill,
                units=units,
                friction=friction,
                is_short=(current_pos == -1),
            )
            exit_notional = units * exit_fill
            total_volume_traded += exit_notional
            if current_pos == 1:
                cash += exit_notional - (exit_notional * friction.commission)
            else:
                cash += gross - (exit_notional * friction.commission)

            trades.append(
                Trade(
                    entry=entry_time_str,
                    exit=f"{all_eval_days[-1].isoformat()} Close",
                    side=Action.BUY if current_pos == 1 else Action.SELL,
                    market=target,
                    pnl=round(net_pnl, 2),
                    note=f"Final bar close out at {exit_fill:.2f}",
                )
            )
            equity_curve[-1] = EquityPoint(t=all_eval_days[-1].isoformat(), v=round(cash, 2))

        # 10. Compute quantitative performance metrics
        perf = compute_full_metrics(
            trades=trades,
            equity=equity_curve,
            total_days=n_days,
            days_exposed=days_exposed,
            total_volume_traded=total_volume_traded,
            initial_capital=self.initial_capital,
        )

        return SimulationResult(
            target_market=target,
            mode=mode,
            allow_short=allow_short,
            initial_capital=self.initial_capital,
            final_equity=perf.end_equity,
            pnl_dollars=perf.pnl_dollars,
            pnl_pct=perf.pnl_pct,
            max_drawdown_pct=perf.max_drawdown_pct,
            hit_rate_pct=perf.hit_rate_pct,
            exposure_pct=perf.exposure_pct,
            exposure_adjusted_return_pct=perf.exposure_adjusted_return_pct,
            sharpe_ratio=perf.sharpe_ratio,
            trade_count=perf.trade_count,
            turnover=perf.turnover,
            evaluation_days_count=n_days,
            degraded_days_count=len(self.degraded_days),
            trades=trades,
            equity_curve=equity_curve,
            daily_decisions=daily_decisions,
            degraded_days=self.degraded_days,
        )
