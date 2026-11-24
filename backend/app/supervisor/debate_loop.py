"""
Supervisor Debate Loop Coordinator.
Moderates Round 0 (Recommendations), Round 1 (Debate & Challenges), and Round 2 (Final Stance).
Enforces max turns cap and detects early consensus.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from app.agents.market_agent import MarketAgent
from app.board.repository import BoardRepository
from app.config.settings import TURN_CAP
from app.domain.enums import Action, Role
from app.domain.models import AgentSummary, Message
from app.supervisor.accuracy import AccuracyTracker
from app.supervisor.consensus import calculate_consensus
from app.supervisor.events import SupervisorEventLog


class DebateLoop:
    def __init__(
        self,
        agents: Dict[str, MarketAgent],
        board: BoardRepository,
        max_turns: int = 3,
        min_margin: float = 0.0,
        accuracy_tracker: AccuracyTracker | None = None,
    ) -> None:
        self.agents = agents
        self.board = board
        self.max_turns = min(max_turns, TURN_CAP)
        self.min_margin = min_margin
        self.accuracy_tracker = accuracy_tracker or AccuracyTracker()
        self.events: List[SupervisorEventLog] = []

    def run(
        self, session_id: str, asset: str
    ) -> Tuple[int, Action, List[AgentSummary], List[SupervisorEventLog]]:
        turns_used = 0

        # --- Round 0: Initial Recommendations ---
        r0_messages: List[Message] = []
        for market, agent in self.agents.items():
            msg = agent.round_0_recommend(session_id, symbol=asset)
            r0_messages.append(msg)

        self.events.append(
            SupervisorEventLog(
                round=0,
                text=f"Supervisor collected {len(r0_messages)} initial recommendations.",
            )
        )

        # Check for immediate unanimity
        initial_positions = {m.from_market: m.position for m in r0_messages}
        if len(set(initial_positions.values())) == 1 and self.max_turns <= 1:
            turns_used = 1
            summaries = self._build_summaries(session_id)
            consensus, _, _ = calculate_consensus(summaries, self.accuracy_tracker)
            return turns_used, consensus, summaries, self.events

        # --- Round 1: Debate & Cross-Market Challenges ---
        turns_used += 1
        challenges_sent: List[Message] = []
        for market, agent in self.agents.items():
            # Review other agents' recommendations
            for other_msg in r0_messages:
                if other_msg.from_market != market:
                    c = agent.round_1_challenge(session_id, other_msg, symbol=asset)
                    if c is not None:
                        challenges_sent.append(c)

        if challenges_sent:
            self.events.append(
                SupervisorEventLog(
                    round=1,
                    text=f"Supervisor routed {len(challenges_sent)} cross-market challenge messages.",
                )
            )

        # Compulsory replies
        replies_sent: List[Message] = []
        for ch in challenges_sent:
            target_agent = self.agents.get(ch.to_market)
            if target_agent:
                rep = target_agent.round_1_reply(session_id, ch, symbol=asset)
                replies_sent.append(rep)

        self.events.append(
            SupervisorEventLog(
                round=1,
                text=f"Compulsory replies received · Logged debate round · Turns = {turns_used}",
            )
        )

        # --- Round 2: Final Stances ---
        turns_used += 1
        all_board_msgs = self.board.get_all(session_id)
        for market, agent in self.agents.items():
            agent.round_2_final(session_id, all_board_msgs, symbol=asset)

        self.events.append(
            SupervisorEventLog(
                round=2,
                text=f"Final positions received · Logged debate round · Turns = {turns_used}",
            )
        )

        summaries = self._build_summaries(session_id)
        consensus, _, _ = calculate_consensus(
            summaries, self.accuracy_tracker, min_margin=self.min_margin
        )
        return turns_used, consensus, summaries, self.events

    def _build_summaries(self, session_id: str) -> List[AgentSummary]:
        summaries: List[AgentSummary] = []
        for market, agent in self.agents.items():
            msgs = [m for m in self.board.get_all(session_id) if m.from_market == market]
            init_pos = msgs[0].position if msgs else agent.state.current_position
            final_pos = agent.state.current_position
            summaries.append(
                AgentSummary(
                    market=market,
                    role=agent.role,
                    initial=init_pos,
                    final=final_pos,
                    confidence=agent.state.confidence,
                    reason=agent.state.last_reason,
                    detail="; ".join(agent.state.evidence) or "Signals neutral",
                )
            )
        return summaries
