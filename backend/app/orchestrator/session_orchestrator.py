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
from app.domain.enums import Action, Mode, MsgType, RiskStatus, Role
from app.domain.models import (
    AgentSummary,
    EquityPoint,
    Message,
    RiskEvent,
    SessionConfig,
    SessionResult,
    Trade,
)
from app.modes.dispatch import run_mode
from app.modes.runner import build_agents, load_markets_config
from app.risk.risk_layer import RiskLayer
from app.simulator.metrics import compute_metrics
from app.simulator.trade_engine import simulate_trades
from app.supervisor import live_accuracy
from app.supervisor.accuracy import AccuracyTracker
from app.supervisor.accuracy_bookkeeper import apply_outcome


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
        self, agents: Dict[str, any], asset: str, session_id: str = ""
    ) -> Tuple[bool, int, int, List[str], List[str]]:
        """
        Quorum Rule: Validates readiness of active agents.
        Returns: (quorum_met, valid_count, total_count, failure_reasons, valid_markets)
        Writes health events and exceptions to the board.
        """
        total_count = len(agents)
        if total_count == 0:
            return False, 0, 0, ["No active agents found in session."], []

        valid_markets: List[str] = []
        reasons: List[str] = []

        for market, agent in agents.items():
            try:
                candles = agent.adapter.get_candles(symbol=asset, limit=10)
                if not candles or len(candles) == 0:
                    r_text = f"{market}: No candle data returned from adapter (market closed / holiday)."
                    reasons.append(r_text)
                    if session_id:
                        self._post_orchestrator_event(
                            session_id=session_id,
                            reason=r_text,
                            evidence=["Zero Candles", "Market Closed"],
                        )
                    continue

                # Test agent recommendation
                pos, conf, reason, _ = agent.brain.recommend(agent.state, candles, agent.knowledge)
                if pos == Action.ABSTAIN and ("empty" in reason.lower() or "missing" in reason.lower()):
                    r_text = f"{market}: Agent abstained due to missing data ({reason})."
                    reasons.append(r_text)
                    if session_id:
                        self._post_orchestrator_event(
                            session_id=session_id,
                            reason=r_text,
                            evidence=["Missing Data ABSTAIN"],
                        )
                    continue

                valid_markets.append(market)
            except TimeoutError as te:
                r_text = f"{market}: Health check timed out: {str(te)}"
                reasons.append(r_text)
                if session_id:
                    self._post_orchestrator_event(
                        session_id=session_id,
                        reason=r_text,
                        evidence=["Agent Timeout"],
                    )
            except Exception as e:
                r_text = f"{market}: Health check raised exception: {type(e).__name__}: {str(e)}"
                reasons.append(r_text)
                if session_id:
                    self._post_orchestrator_event(
                        session_id=session_id,
                        reason=r_text,
                        evidence=[f"Exception: {type(e).__name__}"],
                    )

        valid_count = len(valid_markets)
        quorum_met = (valid_count / total_count) >= 0.5
        return quorum_met, valid_count, total_count, reasons, valid_markets

    def _post_orchestrator_event(
        self,
        session_id: str,
        reason: str,
        round_num: int = 0,
        position: Action = Action.HOLD,
        evidence: Optional[List[str]] = None,
    ) -> Message:
        """Writes an official Orchestrator system message to the board."""
        msg = Message(
            id=f"msg_orch_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            round=round_num,
            from_market="ORCHESTRATOR",
            to_market="BOARD",
            msg_type=MsgType.RECOMMEND,
            position=position,
            confidence=100.0,
            reason=reason,
            evidence=evidence or ["Orchestrator Governance"],
        )
        self.board.add_message(msg)
        return msg

    def run_session(
        self, config: SessionConfig, monitor: bool = True
    ) -> SessionResult:
        """
        Executes a session. If monitor=True, the Orchestrator actively enforces
        quorum gates, agent health checks, and debate quorum (requiring both active agents).
        """
        session_id = f"QRM-{datetime.now(timezone.utc).strftime('%Y')}-{uuid.uuid4().hex}"

        # 1. Build market agents (temporal guard: thread the decision date into
        #    every adapter so the default-deny cutoff is enforced).
        agents = build_agents(
            board=self.board,
            target_market=config.target,
            related_markets=config.related,
            scenario=config.scenario,
            decision_date=config.day,
        )

        now_str = datetime.now(timezone.utc).strftime("%H:%M UTC")

        # 2. Orchestrator Quorum Check (when monitoring is active)
        is_degraded_single = False
        active_target = config.target

        if monitor:
            quorum_met, valid_count, total_count, reasons, valid_markets = self.check_quorum(
                agents=agents, asset=config.asset, session_id=session_id
            )

            # Special Quorum requirement for DEBATE mode:
            # Debate mode requires BOTH active agents to have valid data.
            if config.mode == Mode.DEBATE and total_count >= 2:
                if valid_count == 0:
                    quorum_met = False
                elif valid_count == 1:
                    # Exactly one active agent has valid data (e.g. US holiday while BTC runs)
                    # Trigger degraded single-agent execution!
                    is_degraded_single = True
                    sole_market = valid_markets[0]
                    offline_markets = [m for m in agents if m != sole_market]
                    active_target = sole_market

                    self._post_orchestrator_event(
                        session_id=session_id,
                        reason=(
                            f"Degraded Quorum: Only {sole_market} has valid data ({', '.join(offline_markets)} "
                            "offline / market holiday). Switching to degraded single-agent mode."
                        ),
                        evidence=["Degraded Quorum", "Holiday Fallback"],
                    )

            if not quorum_met:
                fail_summary = (
                    f"Quorum Not Met: only {valid_count} of {total_count} active agents have valid data "
                    "(minimum required not met). Trading halted to HOLD."
                )
                self._post_orchestrator_event(
                    session_id=session_id,
                    reason=fail_summary,
                    evidence=["Quorum Failure"],
                )

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
                    turns_used=0,
                    consensus=Action.HOLD,
                    final_action=Action.HOLD,
                    risk_status=RiskStatus.QUORUM_NOT_MET,
                    risk_note=fail_summary,
                    pnl=0.0,
                    max_drawdown=0.0,
                    win_rate=0.0,
                    timestamp=datetime.now().strftime("%d %b %Y · %H:%M PKT"),
                    messages=visible_msgs,
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

            if not is_degraded_single:
                self._post_orchestrator_event(
                    session_id=session_id,
                    reason=f"Orchestrator health check passed: {valid_count}/{total_count} active agents verified.",
                    evidence=["Health Check Passed"],
                )

        # 3. Execute chosen multi-agent mode.
        effective_mode = Mode.SINGLE if is_degraded_single else config.mode

        # Live accuracy tracker (Part 0.1). Only the live path with a DB handle
        # and a real-data target carries state across sessions; the replay
        # simulator manages its own per-target tracker. Tests run with db=None
        # so they always see a fresh neutral-prior tracker.
        accuracy_tracker = self._prepare_live_tracker(config, active_target, agents)

        turns_used, consensus, summaries, events = run_mode(
            mode=effective_mode,
            agents=agents,
            board=self.board,
            session_id=session_id,
            asset=config.asset,
            max_turns=config.max_turns,
            min_margin=config.min_margin,
            target_market=active_target,
            accuracy_tracker=accuracy_tracker,
        )

        # Record this session's final stances + the target close so the NEXT
        # live session for this target can score this session's calls (no
        # look-ahead: the outcome is applied at the next cutoff).
        if self.db is not None and active_target in ("US", "CRYPTO"):
            ran_markets = {
                m.from_market for m in self.board.get_messages(session_id, round_num=0)
            }
            finals = {
                m: (agents[m].state.current_position, agents[m].state.data_status)
                for m in ran_markets
                if m in agents
            }
            curr_close = self._target_close(agents, active_target, config.asset)
            live_accuracy.set_last(active_target, config.day, curr_close or 0.0, finals)

        # 4. Target candles for risk governance & simulation
        target_adapter = agents[active_target].adapter
        candles = target_adapter.get_candles(symbol=config.asset, limit=100)

        # 5. Risk Layer Evaluation (hard veto authority)
        # For a live session, the running drawdown would need to be computed from
        # DB-persisted equity for this target. The orchestrator does not currently
        # carry equity across sessions, so we pass 0.0 (no drawdown yet). The replay
        # simulator computes and passes the real running drawdown from its equity curve.
        risk_layer = RiskLayer(
            stop_loss=config.stop_loss,
            max_volatility=config.max_vol,
            max_drawdown=config.max_dd,
        )
        final_action, risk_status, risk_note, risk_events, _veto_src = risk_layer.evaluate(
            consensus=consensus,
            candles=candles,
            running_drawdown_pct=0.0,  # live multi-session drawdown requires DB-persisted equity
        )

        if is_degraded_single:
            risk_note = f"Degraded single-agent mode ({active_target}): peer market offline/holiday. {risk_note}"
            risk_events.append(
                RiskEvent(
                    time=now_str,
                    text=f"Degraded single-agent fallback active for {active_target}",
                    level="warn",
                )
            )

        # 6. Simulate trades and metrics
        trades, equity = simulate_trades(
            final_action=final_action,
            target_market=active_target,
            candles=candles,
        )
        pnl, max_dd, win_rate = compute_metrics(trades, equity)

        # 7. Collect board messages with visibility filtering
        raw_msgs = self.board.get_all(session_id)
        open_status = {k: v.get("open", False) for k, v in self.markets_meta.items()}
        visible_msgs = filter_visible_messages(raw_msgs, open_status)

        res = SessionResult(
            id=session_id,
            mode=effective_mode,
            target=active_target,
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

    def _target_close(self, agents: Dict[str, any], target: str, asset: str) -> Optional[float]:
        """Latest closed candle close for the target at the session's decision date."""
        try:
            candles = agents[target].adapter.get_candles(symbol=asset, limit=1)
            return float(candles[-1].close) if candles else None
        except Exception:
            return None

    def _prepare_live_tracker(
        self, config: SessionConfig, active_target: str, agents: Dict[str, any]
    ) -> AccuracyTracker:
        """
        Loads the live accuracy tracker for the traded target and, if a previous
        live session for that target is recorded, applies its outcome (no
        look-ahead) before this session's decision. Returns a fresh tracker for
        the replay/test path (db=None) or non-real targets.
        """
        if self.db is None or active_target not in ("US", "CRYPTO"):
            return AccuracyTracker()

        tracker = live_accuracy.get_tracker(active_target)
        last = live_accuracy.get_last(active_target)
        if last and last.get("close"):
            curr_close = self._target_close(agents, active_target, config.asset)
            if curr_close:
                realised = (curr_close - last["close"]) / last["close"]
                apply_outcome(tracker, last["finals"], realised)
        return tracker

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
