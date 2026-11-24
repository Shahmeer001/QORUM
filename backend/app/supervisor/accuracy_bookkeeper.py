"""
Accuracy bookkeeping shared by the replay simulator and the live orchestrator
(Part 0.1).

Definitions (documented in docs/status/accuracy_protocol.md):
- "Correct" means the agent's directional position matches the SIGN of the
  target asset's realised return over the holding period:
    BUY  (+1) correct  iff realised return > 0
    SELL (-1) correct  iff realised return < 0
    HOLD  ( 0) correct iff realised return == 0 (a flat holding period; in
                       practice this rarely updates, reflecting that a flat
                       stance carries no directional conviction to score)
- realised return = (close[i] - close[i-1]) / close[i-1], where close[k] is the
  TARGET asset's close at the US-close cutoff on evaluation day k. This is the
  return over one decision interval, independent of fill mechanics.
- ABSTAIN calls and non-VALID data (NO_DATA / ERROR / TIMEOUT) are excluded:
  they never update accuracy.
- No look-ahead: the outcome of day t's call is applied only at the next cutoff
  (day t+1), before that day's decision, using close[t] which has just closed.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

from app.domain.enums import Action, DataStatus
from app.supervisor.accuracy import AccuracyTracker


def position_sign(action: Action) -> int:
    if action == Action.BUY:
        return 1
    if action == Action.SELL:
        return -1
    return 0  # HOLD (and ABSTAIN, which is excluded before this is used)


def realised_sign(realised_return: float) -> int:
    if realised_return > 0:
        return 1
    if realised_return < 0:
        return -1
    return 0


def is_correct(action: Action, realised_return: float) -> bool:
    """True iff the agent's position sign equals the realised return sign."""
    return position_sign(action) == realised_sign(realised_return)


def apply_outcome(
    tracker: AccuracyTracker,
    prev_finals: Dict[str, Tuple[Action, DataStatus]],
    realised_return: float,
) -> None:
    """
    Update `tracker` in place with the outcome of the previous decision day.
    `prev_finals` maps market -> (final_action, data_status) from the previous
    session. Only VALID, non-ABSTAIN calls update accuracy.
    """
    for market, (action, data_status) in prev_finals.items():
        if data_status != DataStatus.VALID or action == Action.ABSTAIN:
            continue
        tracker.record_prediction(
            market=market,
            was_correct=is_correct(action, realised_return),
            action=action,
            data_status=DataStatus.VALID,
        )
