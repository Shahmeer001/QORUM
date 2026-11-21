from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models import Message


class BoardRepository(ABC):
    """
    Append-only repository for debate and recommendation messages.
    Interface strictly allows add and read operations only.
    No update or delete operations are permitted.
    """

    @abstractmethod
    def add_message(self, message: Message) -> None:
        """Add a new message to the board."""
        pass

    @abstractmethod
    def get_messages(
        self, session_id: str, round_num: Optional[int] = None
    ) -> List[Message]:
        """Read messages for a session, optionally filtered by round."""
        pass

    @abstractmethod
    def get_all(self, session_id: str) -> List[Message]:
        """Return all messages for the session in insertion order."""
        pass
