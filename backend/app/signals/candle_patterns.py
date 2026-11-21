"""
Candle Pattern Classifier.
Must match research/04_pattern_stats.py labeling logic with SAME_TOLERANCE.
Labels:
  'U' = Up (close > previous close by > tol)
  'S' = Same (|change| <= tol)
  'D' = Down (close < previous close by < -tol)
"""
from __future__ import annotations

from typing import List, Sequence
import numpy as np

from app.config.settings import SAME_TOLERANCE, PATTERN_LENGTH


def label_moves(closes: Sequence[float], tol: float = SAME_TOLERANCE) -> List[str]:
    """
    Labels each candle move vs previous candle close.
    The first element is empty string '' because it has no predecessor.
    """
    c = np.array(closes, dtype=float)
    if len(c) < 2:
        return [""] * len(c)

    change = np.r_[np.nan, c[1:] / c[:-1] - 1.0]
    moves = np.where(change > tol, "U", np.where(change < -tol, "D", "S"))
    moves[0] = ""
    return [str(m) for m in moves]


def extract_recent_pattern(
    closes: Sequence[float], length: int = PATTERN_LENGTH, tol: float = SAME_TOLERANCE
) -> str:
    """
    Extracts the pattern of the last `length` candle moves ending at the last closed candle.
    Format example: 'U-S-D'
    """
    moves = label_moves(closes, tol=tol)
    valid_moves = [m for m in moves if m in ("U", "S", "D")]
    if len(valid_moves) < length:
        # Pad with 'S' if insufficient history
        valid_moves = ["S"] * (length - len(valid_moves)) + valid_moves
    recent = valid_moves[-length:]
    return "-".join(recent)
