"""
In-process accuracy state for LIVE sessions (Part 0.1).

The replay simulator builds a fresh per-target tracker on every run and applies
each day's outcome at the next cutoff inside that run. Live sessions, by
contrast, occur one cutoff at a time across separate requests, so the
previous session's outcome must be carried forward between requests.

This module holds that carry-forward state in-process. It is deliberately
gated to real-data targets (US, CRYPTO) AND to orchestrators that have a
database handle, so the test suite (which runs the orchestrator with db=None)
always sees fresh neutral-prior trackers and stays deterministic. State resets
on process restart; DB persistence of learned accuracy is a documented
follow-up, not a requirement for the FYP1 demo.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

from app.domain.enums import Action, DataStatus
from app.supervisor.accuracy import AccuracyTracker

# target -> the tracker used for that target's live sessions
_TRACKERS: Dict[str, AccuracyTracker] = {}
# target -> {"day": str, "close": float, "finals": {market: (Action, DataStatus)}}
_LAST: Dict[str, Dict] = {}


def get_tracker(target: str) -> AccuracyTracker:
    if target not in _TRACKERS:
        _TRACKERS[target] = AccuracyTracker()
    return _TRACKERS[target]


def get_last(target: str) -> Optional[Dict]:
    return _LAST.get(target)


def set_last(target: str, day: str, close: float, finals: Dict[str, Tuple[Action, DataStatus]]) -> None:
    _LAST[target] = {"day": day, "close": close, "finals": finals}


def reset() -> None:
    """Clear all live accuracy state (used by tests)."""
    _TRACKERS.clear()
    _LAST.clear()
