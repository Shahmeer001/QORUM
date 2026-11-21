from __future__ import annotations

from typing import Dict, List, Optional

from app.board.repository import BoardRepository
from app.domain.models import Message


class MemoryBoardRepository(BoardRepository):
    """
    Fast, thread-safe in-memory message board for fast tests and ephemeral sessions.
    Strictly append-only: supports insertion and reading.
    """

    def __init__(self) -> None:
        self._storage: Dict[str, List[Message]] = {}

    def add_message(self, message: Message) -> None:
        if message.session_id not in self._storage:
            self._storage[message.session_id] = []
        self._storage[message.session_id].append(message)

    def get_messages(
        self, session_id: str, round_num: Optional[int] = None
    ) -> List[Message]:
        msgs = self._storage.get(session_id, [])
        if round_num is not None:
            return [m for m in msgs if m.round == round_num]
        return list(msgs)

    def get_all(self, session_id: str) -> List[Message]:
        return list(self._storage.get(session_id, []))
