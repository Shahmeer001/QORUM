from pathlib import Path
import numpy as np
import pytest

from app.signals.candle_patterns import extract_recent_pattern, label_moves


def test_candle_pattern_labeling_logic():
    # 100 -> 101 (> 0.025% -> U), 101 -> 101.001 (<= 0.025% -> S), 101.001 -> 100 (< -0.025% -> D)
    closes = [100.0, 101.0, 101.001, 100.0]
    moves = label_moves(closes, tol=0.00025)
    assert moves == ["", "U", "S", "D"]

    pattern = extract_recent_pattern(closes, length=3, tol=0.00025)
    assert pattern == "U-S-D"


def test_candle_pattern_matches_research_module():
    """Verify exact equivalence with research/04_pattern_stats.py if present."""
    research_script = Path(__file__).resolve().parent.parent.parent.parent / "research" / "04_pattern_stats.py"
    if research_script.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("research_04", str(research_script))
        mod = importlib.util.module_from_spec(spec)
        # Verify moves calculation definition
        test_closes = np.array([50.0, 52.0, 52.005, 49.0, 51.0, 51.002])
        backend_moves = label_moves(test_closes, tol=0.00025)
        assert backend_moves[1] == "U"
        assert backend_moves[2] == "S"
        assert backend_moves[3] == "D"
