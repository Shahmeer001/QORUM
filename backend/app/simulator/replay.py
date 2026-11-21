"""
Session Playback & Replay Generator.
"""
from __future__ import annotations

from typing import Any, Dict, List
from app.domain.models import Message


def build_replay_timeline(messages: List[Message], events: List[Any]) -> List[Dict[str, Any]]:
    timeline: List[Dict[str, Any]] = []
    rounds = sorted(list({m.round for m in messages}))
    for r in rounds:
        round_msgs = [m.model_dump() for m in messages if m.round == r]
        timeline.append({"round": r, "messages": round_msgs})
    return timeline
