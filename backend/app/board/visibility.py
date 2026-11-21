"""
The No-Look-Ahead Visibility Rule.
Centralized rule ensuring no information leakage across open/closed markets.
"""
from __future__ import annotations

from typing import Dict, List

from app.domain.models import Message


def filter_visible_messages(
    messages: List[Message], market_open_status: Dict[str, bool]
) -> List[Message]:
    """
    Enforces the no-look-ahead rule:
    Only closed-market agents' messages are visible to other agents on the shared board
    to avoid premature leakage from real-time open market noise.
    
    Returns a copy of messages with their `is_visible` flag updated appropriately.
    """
    filtered: List[Message] = []
    for msg in messages:
        # Check if the originating market is open
        is_open = market_open_status.get(msg.from_market, False)
        # Visible if the originating market is closed (or explicitly directed to BOARD)
        # Rule: closed market = visible (!is_open)
        visible = not is_open
        msg_copy = msg.model_copy()
        msg_copy.is_visible = visible
        filtered.append(msg_copy)
    return filtered


def is_market_visible(market: str, market_open_status: Dict[str, bool]) -> bool:
    """Convenience helper: returns True if market is closed (visible on board)."""
    return not market_open_status.get(market, False)
