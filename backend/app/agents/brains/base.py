from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from app.agents.state import AgentState
from app.domain.enums import Action
from app.domain.models import Candle, Message


class Brain(ABC):
    """Abstract interface defining agent cognitive behaviors."""

    @abstractmethod
    def recommend(
        self, state: AgentState, candles: List[Candle], knowledge: Dict[str, Any]
    ) -> Tuple[Action, float, str, List[str]]:
        """Round 0: Initial market recommendation."""
        pass

    @abstractmethod
    def challenge(
        self, state: AgentState, opponent_msg: Message, candles: List[Candle]
    ) -> Optional[Tuple[str, Action, List[str]]]:
        """Round 1: Evaluate opponent message and construct challenge if disagreement exists."""
        pass

    @abstractmethod
    def reply(
        self, state: AgentState, challenge: Message, candles: List[Candle]
    ) -> Tuple[Action, float, str, List[str]]:
        """Round 1: Reply to received challenge."""
        pass

    @abstractmethod
    def final_stance(
        self, state: AgentState, board_messages: List[Message], candles: List[Candle]
    ) -> Tuple[Action, float, str, List[str]]:
        """Round 2: Formulate final position after evaluating all debate arguments."""
        pass
