"""
Session Orchestration Service.
Executes sessions across Single, Silent, and Debate modes with risk gating and simulation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional
import uuid
from sqlalchemy.orm import Session

from app.adapters.synthetic import SyntheticAdapter
from app.board.memory_repo import MemoryBoardRepository
from app.board.sql_repo import SqlBoardRepository
from app.board.visibility import filter_visible_messages
from app.db.tables import SessionTable
from app.domain.enums import Mode, Role
from app.domain.models import SessionConfig, SessionResult
from app.modes.debate import run_debate_mode
from app.modes.runner import build_agents, load_markets_config
from app.modes.silent import run_silent_mode
from app.modes.single import run_single_mode
from app.risk.risk_layer import RiskLayer
from app.simulator.metrics import compute_metrics
from app.simulator.trade_engine import simulate_trades


class SessionService:
    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db
        self.board = SqlBoardRepository(db) if db is not None else MemoryBoardRepository()
        self.markets_meta = load_markets_config()

    def run_session(self, config: SessionConfig) -> SessionResult:
        session_id = f"QRM-{datetime.now(timezone.utc).strftime('%Y')}-{uuid.uuid4().hex[:3].upper()}"
        
        # Build market agents
        agents = build_agents(
            board=self.board,
            target_market=config.target,
            related_markets=config.related,
            scenario=config.scenario,
        )

        # Execute chosen mode
        if config.mode == Mode.SINGLE:
            turns_used, consensus, summaries, events = run_single_mode(
                agents=agents,
                board=self.board,
                session_id=session_id,
                target_market=config.target,
                asset=config.asset,
            )
        elif config.mode == Mode.SILENT:
            turns_used, consensus, summaries, events = run_silent_mode(
                agents=agents,
                board=self.board,
                session_id=session_id,
                asset=config.asset,
            )
        else:  # Mode.DEBATE
            turns_used, consensus, summaries, events = run_debate_mode(
                agents=agents,
                board=self.board,
                session_id=session_id,
                asset=config.asset,
                max_turns=config.max_turns,
            )

        # Retrieve target candles for risk evaluation & simulation
        target_adapter = agents[config.target].adapter
        candles = target_adapter.get_candles(symbol=config.asset, limit=100)

        # Evaluate through Risk Layer (hard veto authority)
        risk_layer = RiskLayer(
            stop_loss=config.stop_loss,
            max_volatility=config.max_vol,
            max_drawdown=config.max_dd,
        )
        final_action, risk_status, risk_note, risk_events = risk_layer.evaluate(
            consensus=consensus,
            candles=candles,
        )

        # Simulate trades and equity curve
        trades, equity = simulate_trades(
            final_action=final_action,
            target_market=config.target,
            candles=candles,
        )
        pnl, max_dd, win_rate = compute_metrics(trades, equity)

        # Messages from board
        raw_msgs = self.board.get_all(session_id)
        open_status = {k: v.get("open", False) for k, v in self.markets_meta.items()}
        visible_msgs = filter_visible_messages(raw_msgs, open_status)

        res = SessionResult(
            id=session_id,
            mode=config.mode,
            target=config.target,
            asset=config.asset,
            horizon=config.horizon,
            day=config.day,
            max_turns=config.max_turns,
            turns_used=turns_used,
            consensus=consensus,
            final_action=final_action,
            risk_status=risk_status,
            risk_note=risk_note,
            pnl=pnl,
            max_drawdown=max_dd,
            win_rate=win_rate,
            timestamp=datetime.now().strftime("%d %b %Y · %H:%M PKT"),
            messages=visible_msgs,
            agents=summaries,
            trades=trades,
            equity=equity,
            risk_events=risk_events,
        )

        # Persist session row if DB attached
        if self.db is not None:
            s_row = SessionTable(
                id=res.id,
                mode=res.mode.value,
                target_market=res.target,
                asset=res.asset,
                horizon=res.horizon,
                day=res.day,
                max_turns=res.max_turns,
                turns_used=res.turns_used,
                consensus_action=res.consensus.value,
                final_action=res.final_action.value,
                risk_status=res.risk_status.value,
                risk_note=res.risk_note,
                pnl=res.pnl,
                max_drawdown=res.max_drawdown,
                win_rate=res.win_rate,
            )
            self.db.add(s_row)
            self.db.commit()

        return res
