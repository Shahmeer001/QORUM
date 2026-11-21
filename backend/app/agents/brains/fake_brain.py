"""
Fake / Deterministic Mock Brain for Quick Unit Tests and Demonstrations.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.agents.brains.base import Brain
from app.agents.state import AgentState
from app.domain.enums import Action
from app.domain.models import Candle, Message


class FakeBrain(Brain):
    def __init__(self, forced_action: Action = Action.BUY) -> None:
        self.forced_action = forced_action

    def recommend(
        self, state: AgentState, candles: List[Candle], knowledge: Dict[str, Any]
    ) -> Tuple[Action, float, str, List[str]]:
        return self.forced_action, 75.0, "Mock recommendation from fake brain.", ["Mock signal 1"]

    def challenge(
        self, state: AgentState, opponent_msg: Message, candles: List[Candle]
    ) -> Optional[Tuple[str, Action, List[str]]]:
        if opponent_msg.position != self.forced_action:
            return "Mock challenge to opponent.", Action.HOLD, ["Mock challenge evidence"]
        return None

    def reply(
        self, state: AgentState, challenge: Message, candles: List[Candle]
    ) -> Tuple[Action, float, str, List[str]]:
        return Action.HOLD, 60.0, "Mock reply conceding to hold.", ["Mock reply evidence"]

    def final_stance(
        self, state: AgentState, board_messages: List[Message], candles: List[Candle]
    ) -> Tuple[Action, float, str, List[str]]:
        return self.forced_action, 70.0, "Mock final position.", ["Mock final evidence"]
