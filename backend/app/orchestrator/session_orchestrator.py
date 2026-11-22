"""
QUORUM Session Orchestrator.
The governing third agent that monitors market agents, enforces the Quorum Rule,
coordinates structured debate or silent modes, and oversees risk validation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import uuid
from sqlalchemy.orm import Session

from app.board.memory_repo import MemoryBoardRepository
from app.board.repository import BoardRepository
from app.board.sql_repo import SqlBoardRepository
from app.board.visibility import filter_visible_messages
from app.db.tables import SessionTable
from app.domain.enums import Action, Mode, RiskStatus, Role
from app.domain.models import (
    AgentSummary,
    EquityPoint,
    Message,
    RiskEvent,
    SessionConfig,
    SessionResult,
    Trade,
)
from app.modes.debate import run_debate_mode
from app.modes.runner import build_agents, load_markets_config
from app.modes.silent import run_silent_mode
from app.modes.single import run_single_mode
from app.risk.risk_layer import RiskLayer
from app.simulator.metrics import compute_metrics
from app.simulator.trade_engine import simulate_trades


class SessionOrchestrator:
    """
    Orchestrator Agent.
    Monitors active market agents, validates data readiness, enforces quorum,
    and governs session execution.
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        board: Optional[BoardRepository] = None,
    ) -> None:
        self.db = db
        if board is not None:
            self.board = board
        elif db is not None:
            self.board = SqlBoardRepository(db)
        else:
            self.board = MemoryBoardRepository()
        self.markets_meta = load_markets_config()

    def check_quorum(
        self, agents: Dict[str, any], asset: str
    ) -> Tuple[bool, int, int, List[str]]:
        """
        Quorum Rule: At least 50% of active agents must have valid data/recommendations.
        Returns: (quorum_met, valid_count, total_count, failure_reasons)
        """
        total_count = len(agents)
        if total_count == 0:
            return False, 0, 0, ["No active agents found in session."]

        valid_count = 0
        reasons: List[str] = []

        for market, agent in agents.items():
            try:
                candles = agent.adapter.get_candles(symbol=asset, limit=10)
                if not candles or len(candles) == 0:
                    reasons.append(f"{market}: No candle data returned from adapter.")
                    continue

                # Check if recommendation produces a valid position (not ABSTAIN due to empty/invalid data)
                pos, conf, reason, _ = agent.brain.recommend(agent.state, candles, agent.knowledge)
                if pos == Action.ABSTAIN and ("empty" in reason.lower() or "missing" in reason.lower()):
                    reasons.append(f"{market}: Agent abstained due to missing data ({reason}).")
                    continue

                valid_count += 1
            except Exception as e:
                reasons.append(f"{market}: Data check raised exception: {str(e)}")

        quorum_met = (valid_count / total_count) >= 0.5
        return quorum_met, valid_count, total_count, reasons

    def run_session(
        self, config: SessionConfig, monitor: bool = True
    ) -> SessionResult:
        """
        Executes a session. If monitor=True, the Orchestrator actively enforces
        quorum gates and agent health checks. If monitor=False, runs raw multi-agent
        execution without orchestrator monitoring.
        """
        session_id = f"QRM-{datetime.now(timezone.utc).strftime('%Y')}-{uuid.uuid4().hex[:3].upper()}"

        # 1. Build market agents
        agents = build_agents(
            board=self.board,
            target_market=config.target,
            related_markets=config.related,
            scenario=config.scenario,
        )

        # 2. Orchestrator Quorum Check (when monitoring is active)
        if monitor:
            quorum_met, valid_count, total_count, reasons = self.check_quorum(
                agents=agents, asset=config.asset
            )
            if not quorum_met:
                now_str = datetime.now(timezone.utc).strftime("%H:%M UTC")
                fail_summary = f"Quorum Not Met: only {valid_count} of {total_count} active agents have valid data (minimum 50% required). Trading halted to HOLD."
                
                # Build agent summaries showing current state / abstain
                agent_summaries: List[AgentSummary] = []
                for m, ag in agents.items():
                    agent_summaries.append(
                        AgentSummary(
                            market=m,
                            role=ag.role,
                            initial=Action.ABSTAIN,
                            final=Action.ABSTAIN,
                            confidence=0.0,
                            reason="Quorum check failed: insufficient market data.",
                            detail=f"Valid count: {valid_count}/{total_count}",
                        )
                    )

                res = SessionResult(
                    id=session_id,
                    mode=config.mode,
                    target=config.target,
                    asset=config.asset,
                    horizon=config.horizon,
                    day=config.day,
                    max_turns=config.max_turns,
                    turns_used=0,
                    consensus=Action.HOLD,
                    final_action=Action.HOLD,
                    risk_status=RiskStatus.QUORUM_NOT_MET,
                    risk_note=fail_summary,
                    pnl=0.0,
                    max_drawdown=0.0,
                    win_rate=0.0,
                    timestamp=datetime.now().strftime("%d %b %Y · %H:%M PKT"),
                    messages=[],
                    agents=agent_summaries,
                    trades=[],
                    equity=[EquityPoint(t="0", v=100.0)],
                    risk_events=[
                        RiskEvent(
                            time=now_str,
                            text=f"Orchestrator Quorum Failure ({valid_count}/{total_count} agents valid) -> halted to HOLD",
                            level="override",
                        )
                    ],
                )

                if self.db is not None:
                    self._persist_session(res)
                return res

        # 3. Execute chosen multi-agent mode
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

        # 4. Target candles for risk governance & simulation
        target_adapter = agents[config.target].adapter
        candles = target_adapter.get_candles(symbol=config.asset, limit=100)

        # 5. Risk Layer Evaluation (hard veto authority)
        risk_layer = RiskLayer(
            stop_loss=config.stop_loss,
            max_volatility=config.max_vol,
            max_drawdown=config.max_dd,
        )
        final_action, risk_status, risk_note, risk_events = risk_layer.evaluate(
            consensus=consensus,
            candles=candles,
        )

        # 6. Simulate trades and metrics
        trades, equity = simulate_trades(
            final_action=final_action,
            target_market=config.target,
            candles=candles,
        )
        pnl, max_dd, win_rate = compute_metrics(trades, equity)

        # 7. Collect board messages with visibility filtering
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

        if self.db is not None:
            self._persist_session(res)

        return res

    def run_monitored(self, config: SessionConfig) -> SessionResult:
        """Executes session with active Orchestrator monitoring."""
        return self.run_session(config=config, monitor=True)

    def run_unmonitored(self, config: SessionConfig) -> SessionResult:
        """Executes session without Orchestrator monitoring (raw multi-agent execution)."""
        return self.run_session(config=config, monitor=False)

    def _persist_session(self, res: SessionResult) -> None:
        if self.db is None:
            return
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
