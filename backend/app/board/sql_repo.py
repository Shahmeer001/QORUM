"""
SQL-backed Board Repository.
Appends and reads messages using SQLite/SQLAlchemy.
"""
from __future__ import annotations

import json
from typing import List, Optional
from sqlalchemy.orm import Session

from app.board.repository import BoardRepository
from app.db.tables import MessageTable
from app.domain.enums import Action, MsgType
from app.domain.models import Message


class SqlBoardRepository(BoardRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_message(self, message: Message) -> None:
        row = MessageTable(
            id=message.id,
            session_id=message.session_id,
            round=message.round,
            from_market=message.from_market,
            to_market=message.to_market,
            msg_type=message.msg_type.value,
            position=message.position.value,
            confidence=message.confidence,
            reason=message.reason,
            evidence_json=json.dumps(message.evidence),
            is_visible=1 if message.is_visible else 0,
        )
        self.db.add(row)
        self.db.commit()

    def get_messages(
        self, session_id: str, round_num: Optional[int] = None
    ) -> List[Message]:
        q = self.db.query(MessageTable).filter(MessageTable.session_id == session_id)
        if round_num is not None:
            q = q.filter(MessageTable.round == round_num)
        rows = q.order_by(MessageTable.created_at.asc()).all()
        return [self._to_model(r) for r in rows]

    def get_all(self, session_id: str) -> List[Message]:
        rows = (
            self.db.query(MessageTable)
            .filter(MessageTable.session_id == session_id)
            .order_by(MessageTable.created_at.asc())
            .all()
        )
        return [self._to_model(r) for r in rows]

    def update_message(self, message: Message) -> None:
        """Reject attempts to edit or mutate existing messages."""
        raise PermissionError("SqlBoardRepository is append-only: message updates are strictly prohibited.")

    def delete_message(self, message_id: str) -> None:
        """Reject attempts to delete messages."""
        raise PermissionError("SqlBoardRepository is append-only: message deletions are strictly prohibited.")

    def _to_model(self, r: MessageTable) -> Message:
        ev = json.loads(r.evidence_json) if r.evidence_json else []
        return Message(
            id=r.id,
            session_id=r.session_id,
            round=r.round,
            from_market=r.from_market,
            to_market=r.to_market,
            msg_type=MsgType(r.msg_type),
            position=Action(r.position),
            confidence=r.confidence,
            reason=r.reason,
            evidence=ev,
            is_visible=bool(r.is_visible),
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
