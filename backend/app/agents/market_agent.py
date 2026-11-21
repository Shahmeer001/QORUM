"""
Market Agent Implementation.
One class, instantiated once per market (PSX, US, FOREX, GOLD, CRYPTO).
Enforces isolation: an agent cannot directly request another market's proprietary data.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from app.adapters.base import MarketDataAdapter
from app.agents.brains.base import Brain
from app.agents.brains.rule_brain import RuleBrain
from app.agents.brains.fake_brain import FakeBrain
from app.agents.state import AgentState
from app.board.repository import BoardRepository
from app.config.settings import BRAIN
from app.domain.enums import Action, MsgType, Role
from app.domain.models import Candle, Message
from app.signals.knowledge_loader import load_market_knowledge


class MarketAgent:
    def __init__(
        self,
        market: str,
        adapter: MarketDataAdapter,
        board: BoardRepository,
        role: Role = Role.RELATED,
        brain: Brain | None = None,
    ) -> None:
        self.market = market
        self.adapter = adapter
        self.board = board
        self.role = role
        self.state = AgentState(market=market, role=role)

        if brain is not None:
            self.brain = brain
        else:
            self.brain = FakeBrain() if BRAIN == "fake" else RuleBrain()

        self.knowledge = load_market_knowledge(market)

    def _fetch_own_candles(self, symbol: str) -> List[Candle]:
        """Fetch own proprietary candles — isolation is strictly enforced."""
        return self.adapter.get_candles(symbol=symbol, limit=100)

    def round_0_recommend(self, session_id: str, symbol: str) -> Message:
        candles = self._fetch_own_candles(symbol)
        pos, conf, reason, ev = self.brain.recommend(self.state, candles, self.knowledge)
        self.state.current_position = pos
        self.state.confidence = conf
        self.state.last_reason = reason
        self.state.evidence = ev

        msg = Message(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            round=0,
            from_market=self.market,
            to_market="BOARD",
            msg_type=MsgType.RECOMMEND,
            position=pos,
            confidence=conf,
            reason=reason,
            evidence=ev,
        )
        self.board.add_message(msg)
        return msg

    def round_1_challenge(
        self, session_id: str, opponent_msg: Message, symbol: str
    ) -> Optional[Message]:
        candles = self._fetch_own_candles(symbol)
        res = self.brain.challenge(self.state, opponent_msg, candles)
        if res is None:
            return None

        reason, suggested_pos, ev = res
        msg = Message(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            round=1,
            from_market=self.market,
            to_market=opponent_msg.from_market,
            msg_type=MsgType.CHALLENGE,
            position=suggested_pos,
            confidence=self.state.confidence,
            reason=reason,
            evidence=ev,
        )
        self.board.add_message(msg)
        return msg

    def round_1_reply(
        self, session_id: str, challenge_msg: Message, symbol: str
    ) -> Message:
        candles = self._fetch_own_candles(symbol)
        pos, conf, reason, ev = self.brain.reply(self.state, challenge_msg, candles)
        self.state.current_position = pos
        self.state.confidence = conf
        self.state.last_reason = reason
        self.state.evidence = ev

        msg = Message(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            round=1,
            from_market=self.market,
            to_market=challenge_msg.from_market,
            msg_type=MsgType.REPLY,
            position=pos,
            confidence=conf,
            reason=reason,
            evidence=ev,
        )
        self.board.add_message(msg)
        return msg

    def round_2_final(
        self, session_id: str, board_messages: List[Message], symbol: str
    ) -> Message:
        candles = self._fetch_own_candles(symbol)
        pos, conf, reason, ev = self.brain.final_stance(
            self.state, board_messages, candles
        )
        self.state.current_position = pos
        self.state.confidence = conf
        self.state.last_reason = reason
        self.state.evidence = ev

        msg = Message(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            round=2,
            from_market=self.market,
            to_market="BOARD",
            msg_type=MsgType.FINAL,
            position=pos,
            confidence=conf,
            reason=reason,
            evidence=ev,
        )
        self.board.add_message(msg)
        return msg
