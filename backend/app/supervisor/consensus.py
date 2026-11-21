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
    agents: List[AgentSummary], accuracy_tracker: AccuracyTracker
) -> Tuple[Action, float, Dict[str, float]]:
    """
    Computes winning Action and consensus confidence percentage.
    """
    scores: Dict[Action, float] = {
        Action.BUY: 0.0,
        Action.SELL: 0.0,
        Action.HOLD: 0.0,
        Action.ABSTAIN: 0.0,
    }

    total_weight = 0.0
    for a in agents:
        w = accuracy_tracker.get_weight(a.market, a.role)
        scores[a.final] += w * (a.confidence / 100.0)
        total_weight += w

    if total_weight <= 0:
        return Action.HOLD, 50.0, {k.value: 0.0 for k in scores}

    # Normalize
    distribution = {k.value: round((v / total_weight) * 100.0, 1) for k, v in scores.items()}
    winning_action = max(scores.keys(), key=lambda k: scores[k])
    winning_confidence = distribution[winning_action.value]

    return winning_action, winning_confidence, distribution
