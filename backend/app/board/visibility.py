"""
The Visibility & No-Look-Ahead Rule.
Decides which messages and candles a given reader may see.

Design Decision:
1. Decision time per day is just after the US close (4:00 PM America/New_York converted to UTC).
2. Data cut-off: each adapter/feed returns only candles that have closed at or before that decision time.
3. Rounds: in debate round r, an agent sees only messages from earlier rounds (< r) and its own messages from round r.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Sequence, Tuple
from dateutil import parser

from app.domain.models import Candle, Message


def parse_datetime_utc(ts: str | datetime) -> datetime:
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    dt = parser.parse(ts)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def is_candle_visible(candle: Candle, decision_time_utc: datetime) -> bool:
    """
    A candle that closes after the decision cutoff time is NEVER returned.
    """
    candle_ts = parse_datetime_utc(candle.timestamp)
    return candle_ts <= decision_time_utc


def is_message_visible_to_reader(
    message: Message,
    reader_market: str,
    current_round: int,
) -> bool:
    """
    In debate round r, an agent sees only messages from earlier rounds (< r) and its own.
    A message from the current round from another agent is invisible.
    """
    if message.round < current_round:
        return True
    if message.round == current_round:
        return message.from_market == reader_market or message.sender == reader_market
    return False


def filter_visible_data(
    reader_market: str,
    current_round: int,
    decision_time_utc: datetime,
    messages: Sequence[Message] | None = None,
    candles: Sequence[Candle] | None = None,
) -> Tuple[List[Message], List[Candle]]:
    """
    Single unified function that decides which messages and candles a given reader may see.
    """
    visible_msgs: List[Message] = []
    if messages is not None:
        visible_msgs = [
            m for m in messages
            if is_message_visible_to_reader(m, reader_market, current_round)
        ]

    visible_candles: List[Candle] = []
    if candles is not None:
        visible_candles = [
            c for c in candles
            if is_candle_visible(c, decision_time_utc)
        ]

    return visible_msgs, visible_candles


def filter_visible_messages(
    messages: List[Message], market_open_status: Dict[str, bool]
) -> List[Message]:
    """
    Backward-compatible helper for UI display: closed markets visible.
    """
    filtered: List[Message] = []
    for msg in messages:
        is_open = market_open_status.get(msg.from_market, False)
        visible = not is_open
        msg_copy = msg.model_copy()
        msg_copy.is_visible = visible
        filtered.append(msg_copy)
    return filtered
