"""
Supervisor Weighted Consensus Calculation.
Aggregates agent votes weighted by role and historical accuracy.
"""
from __future__ import annotations

from typing import Dict, List, Tuple
from app.domain.enums import Action, Role
from app.domain.models import AgentSummary
from app.supervisor.accuracy import AccuracyTracker


def calculate_consensus(
    agents: List[AgentSummary],
    accuracy_tracker: AccuracyTracker,
    min_margin: float = 0.0,
    unweighted: bool = False,
) -> Tuple[Action, float, Dict[str, float]]:
    """
    Computes winning Action and consensus confidence percentage.

    Weighting (Part 0.2):
    - unweighted=False (silent-weighted / debate): vote weight = role x learned
      accuracy (via accuracy_tracker.get_weight), then scaled by confidence.
    - unweighted=True (silent-unweighted): equal votes -- every agent gets a
      base weight of 1.0 (no role, no accuracy), still scaled by its own
      confidence. This isolates the effect of role x accuracy weighting.

    If min_margin > 0.0 and the top directional score does not beat the runner-up
    by at least min_margin percentage points, consensus defaults to HOLD.
    A directional BUY/SELL tie also resolves to HOLD.
    """
    scores: Dict[Action, float] = {
        Action.BUY: 0.0,
        Action.SELL: 0.0,
        Action.HOLD: 0.0,
        Action.ABSTAIN: 0.0,
    }

    total_weight = 0.0
    for a in agents:
        if unweighted:
            w = 1.0
        else:
            w = accuracy_tracker.get_weight(a.market, a.role)
        scores[a.final] += w * (a.confidence / 100.0)
        total_weight += w

    if total_weight <= 0:
        return Action.HOLD, 50.0, {k.value: 0.0 for k in scores}

    # Normalize
    distribution = {k.value: round((v / total_weight) * 100.0, 1) for k, v in scores.items()}

    # Resolve directional ties (BUY vs SELL) to HOLD
    buy_score = scores[Action.BUY]
    sell_score = scores[Action.SELL]
    max_val = max(scores.values())

    # Sort actions by score descending
    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_action, top_score = sorted_scores[0]
    runner_up_action, runner_up_score = sorted_scores[1]

    # Margin check between top score and runner up in normalized percentage points
    lead_margin = distribution[top_action.value] - distribution[runner_up_action.value]

    if max_val > 0.0 and buy_score == sell_score and buy_score == max_val:
        winning_action = Action.HOLD
        winning_confidence = distribution[Action.HOLD.value]
    elif min_margin > 0.0 and top_action in (Action.BUY, Action.SELL) and lead_margin < min_margin:
        winning_action = Action.HOLD
        winning_confidence = distribution[Action.HOLD.value]
    else:
        winning_action = max(scores.keys(), key=lambda k: scores[k])
        winning_confidence = distribution[winning_action.value]

    return winning_action, winning_confidence, distribution
