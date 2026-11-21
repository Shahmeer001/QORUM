from __future__ import annotations

from typing import Dict, List, Optional

from app.board.repository import BoardRepository
from app.domain.models import Message


class MemoryBoardRepository(BoardRepository):
    """
    Fast, in-memory message board.
    Strictly append-only: supports insertion and reading.
    Any attempt to edit or delete a message is explicitly rejected.
    """

    def __init__(self) -> None:
        self._storage: Dict[str, List[Message]] = {}

    def add_message(self, message: Message) -> None:
        if message.session_id not in self._storage:
            self._storage[message.session_id] = []
        # Store an immutable clone so callers cannot mutate stored messages
        self._storage[message.session_id].append(message.model_copy(deep=True))

    def get_messages(
        self, session_id: str, round_num: Optional[int] = None
    ) -> List[Message]:
        msgs = self._storage.get(session_id, [])
        if round_num is not None:
            return [m.model_copy(deep=True) for m in msgs if m.round == round_num]
        return [m.model_copy(deep=True) for m in msgs]

    def get_all(self, session_id: str) -> List[Message]:
        return [m.model_copy(deep=True) for m in self._storage.get(session_id, [])]

    # Explicit rejection of edit or delete operations to protect audit integrity
    def update_message(self, *args, **kwargs) -> None:
        raise PermissionError("Board repository is append-only: updates are prohibited.")

    def delete_message(self, *args, **kwargs) -> None:
        raise PermissionError("Board repository is append-only: deletions are prohibited.")
