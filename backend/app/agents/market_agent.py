"""
Market Agent Implementation.
One class, instantiated once per market (PSX, US, FOREX, GOLD, CRYPTO).
Enforces isolation: an agent cannot directly request another market's proprietary data.
"""
from __future__ import annotations

import concurrent.futures
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.adapters.base import MarketDataAdapter
from app.agents.brains.base import Brain
from app.agents.brains.rule_brain import RuleBrain
from app.agents.brains.fake_brain import FakeBrain
from app.agents.state import AgentState
from app.board.repository import BoardRepository
from app.config.settings import AGENT_TIMEOUT_SECONDS, BRAIN
from app.domain.enums import Action, DataStatus, MsgType, Role
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
        timeout: float = AGENT_TIMEOUT_SECONDS,
    ) -> None:
        self.market = market
        self.adapter = adapter
        self.board = board
        self.role = role
        self.timeout = timeout
        self.state = AgentState(market=market, role=role)

        if brain is not None:
            self.brain = brain
        else:
            self.brain = FakeBrain() if BRAIN == "fake" else RuleBrain()

        self.knowledge = load_market_knowledge(market)

    def _execute_with_safety(self, func: Callable[[], Any]) -> Any:
        """Executes a function with strict timeout and exception wrapping."""
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func)
                return future.result(timeout=self.timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"Agent {self.market} timed out after {self.timeout}s.")
        except Exception as e:
            raise e

    def _fetch_own_candles(self, symbol: str) -> List[Candle]:
        """Fetch own proprietary candles — isolation is strictly enforced."""
        return self.adapter.get_candles(symbol=symbol, limit=100)

    def round_0_recommend(self, session_id: str, symbol: str) -> Message:
        data_status = DataStatus.VALID
        try:
            candles = self._execute_with_safety(lambda: self._fetch_own_candles(symbol))
            if not candles:
                data_status = DataStatus.NO_DATA
            pos, conf, reason, ev = self._execute_with_safety(
                lambda: self.brain.recommend(self.state, candles, self.knowledge)
            )
            if pos == Action.ABSTAIN:
                data_status = DataStatus.NO_DATA
        except TimeoutError as te:
            pos, conf = Action.ABSTAIN, 0.0
            data_status = DataStatus.TIMEOUT
            reason = f"TimeoutError: Agent {self.market} execution timed out ({str(te)})."
            ev = ["Agent Timeout"]
        except Exception as e:
            pos, conf = Action.ABSTAIN, 0.0
            data_status = DataStatus.ERROR
            reason = f"Exception: Agent {self.market} failed with {type(e).__name__}: {str(e)}"
            ev = [f"Exception: {type(e).__name__}"]

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
            data_status=data_status,
        )
        self.board.add_message(msg)
        return msg

    def round_1_challenge(
        self, session_id: str, opponent_msg: Message, symbol: str
    ) -> Optional[Message]:
        try:
            candles = self._execute_with_safety(lambda: self._fetch_own_candles(symbol))
            res = self._execute_with_safety(
                lambda: self.brain.challenge(self.state, opponent_msg, candles)
            )
        except Exception:
            return None

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
        try:
            candles = self._execute_with_safety(lambda: self._fetch_own_candles(symbol))
            pos, conf, reason, ev = self._execute_with_safety(
                lambda: self.brain.reply(self.state, challenge_msg, candles)
            )
        except TimeoutError as te:
            pos, conf = Action.ABSTAIN, 0.0
            reason = f"TimeoutError: Agent {self.market} reply timed out."
            ev = ["Agent Timeout"]
        except Exception as e:
            pos, conf = Action.ABSTAIN, 0.0
            reason = f"Exception: Agent {self.market} reply failed: {type(e).__name__}: {str(e)}"
            ev = ["Exception"]

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
        try:
            candles = self._execute_with_safety(lambda: self._fetch_own_candles(symbol))
            pos, conf, reason, ev = self._execute_with_safety(
                lambda: self.brain.final_stance(self.state, board_messages, candles)
            )
        except TimeoutError as te:
            pos, conf = Action.ABSTAIN, 0.0
            reason = f"TimeoutError: Agent {self.market} final stance timed out."
            ev = ["Agent Timeout"]
        except Exception as e:
            pos, conf = Action.ABSTAIN, 0.0
            reason = f"Exception: Agent {self.market} final stance failed: {type(e).__name__}: {str(e)}"
            ev = ["Exception"]

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
