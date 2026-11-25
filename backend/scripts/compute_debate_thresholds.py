"""
Debate volatility thresholds: each agent's 90th percentile of its own volatility
measure on the LEARNING window only (protocol.md section 12).
Writes app/config/debate_thresholds.json.

--test-run: same rule on 2022-2024 (protocol.md section 13), written to
app/config/debate_thresholds_test.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.adapters.binance_btc import BinanceBTCAdapter
from app.adapters.us_spy import USMarketAdapter
from app.signals.volatility import calculate_realized_volatility
from app.simulator.replay_simulator import BarByBarSimulator

LEARN_START, LEARN_END = "2022-01-03", "2023-12-31"
PERCENTILE = 90
OUT = Path(__file__).resolve().parent.parent / "app" / "config" / "debate_thresholds.json"


def main() -> None:
    test_run = "--test-run" in sys.argv[1:]
    end = "2024-12-31" if test_run else LEARN_END
    out = OUT.with_name("debate_thresholds_test.json") if test_run else OUT

    class _LearningDays(BarByBarSimulator):
        TEST_START, TEST_END = LEARN_START, end

    days = _LearningDays().evaluation_days
    assert days and days[-1].isoformat() <= end
    thresholds = {}
    for market, adapter in (("US", USMarketAdapter()), ("CRYPTO", BinanceBTCAdapter())):
        vols = []
        for d in days:
            adapter.current_date = d.isoformat()
            candles = adapter.get_candles(limit=100)
            if candles:
                vols.append(calculate_realized_volatility([c.close for c in candles]))
        thresholds[market] = round(float(np.percentile(vols, PERCENTILE)), 4)
    out.write_text(json.dumps({
        "window": [LEARN_START, end],
        "percentile": PERCENTILE,
        "decision_days": len(days),
        "thresholds": thresholds,
    }, indent=2) + "\n", encoding="utf-8")
    print(thresholds)


if __name__ == "__main__":
    main()
