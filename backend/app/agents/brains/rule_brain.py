"""
Deterministic Rule-Based Agent Brain.
Implements written challenge and reply rules grounded in technical signals and pattern knowledge.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.agents.brains.base import Brain
from app.agents.state import AgentState
from app.domain.enums import Action, Role
from app.domain.models import Candle, Message
from app.signals.candle_patterns import extract_recent_pattern
from app.signals.rsi import calculate_rsi
from app.signals.volatility import calculate_realized_volatility


class RuleBrain(Brain):
    def recommend(
        self, state: AgentState, candles: List[Candle], knowledge: Dict[str, Any]
    ) -> Tuple[Action, float, str, List[str]]:
        closes = [c.close for c in candles]
        rsi = calculate_rsi(closes)
        vol = calculate_realized_volatility(closes)
        pat = extract_recent_pattern(closes)

        # Pattern lift
        patterns = knowledge.get("patterns", {})
        pat_stat = patterns.get(pat, {})
        lift = pat_stat.get("lift", 1.0)

        # Baseline momentum vs oversold / overbought checks
        evidence: List[str] = [f"RSI {rsi:.1f}", f"Pattern {pat}", f"Vol {vol:.1f}%"]

        recent_return = (closes[-1] / closes[0] - 1.0) * 100.0 if closes else 0.0

        # Bullish signal: positive trend or oversold bounce
        if (recent_return > 0.5 and rsi > 45.0) or rsi < 30.0 or (pat in ("U-U-U", "D-S-U") and lift >= 1.15):
            pos = Action.BUY
            conf = min(85.0, 60.0 + (lift - 1.0) * 20.0)
            reason = f"Bullish structure confirmed with pattern {pat} (lift {lift:.2f}x); RSI at {rsi:.1f}."
            evidence.append("Bullish momentum")
        # Bearish signal: negative trend with breakdown
        elif (recent_return < -0.5 and rsi < 55.0) or rsi > 80.0 or (pat in ("D-D-D", "U-S-D") and vol > 2.0):
            pos = Action.SELL
            conf = min(85.0, 60.0 + abs(recent_return) * 2.0)
            reason = f"Bearish breakdown with pattern {pat} and elevated risk; taking short / defensive stance."
            evidence.append(f"Bearish trend ({recent_return:.1f}%)")
        else:
            pos = Action.HOLD
            conf = 55.0
            reason = f"Price consolidating around {closes[-1]:.2f}; signals neutral (RSI {rsi:.1f})."

        return pos, round(conf, 1), reason, evidence

    def challenge(
        self, state: AgentState, opponent_msg: Message, candles: List[Candle]
    ) -> Optional[Tuple[str, Action, List[str]]]:
        if opponent_msg.position != state.current_position and opponent_msg.position != Action.HOLD:
            closes = [c.close for c in candles]
            vol = calculate_realized_volatility(closes)
            rsi = calculate_rsi(closes)

            if opponent_msg.position == Action.BUY and (vol > 2.0 or rsi > 70.0):
                reason = (
                    f"Warning to {opponent_msg.from_market}: Breakout lacks cross-market confirmation. "
                    f"Macro volatility is elevated at {vol:.1f}%."
                )
                return reason, Action.HOLD, [f"Vol {vol:.1f}%", f"Opponent {opponent_msg.position}"]

            if opponent_msg.position == Action.SELL and rsi < 35.0:
                reason = (
                    f"Challenge to {opponent_msg.from_market}: Downside momentum is slowing with RSI at {rsi:.1f}. "
                    "Risk of selling the bottom."
                )
                return reason, Action.HOLD, [f"RSI {rsi:.1f}"]

        return None

    def reply(
        self, state: AgentState, challenge: Message, candles: List[Candle]
    ) -> Tuple[Action, float, str, List[str]]:
        closes = [c.close for c in candles]
        vol = calculate_realized_volatility(closes)
        rsi = calculate_rsi(closes)

        if vol > 2.4:
            new_pos = Action.HOLD
            conf = 58.0
            reason = (
                f"Accepted warning from {challenge.from_market}. Volatility ({vol:.1f}%) warrants caution; "
                "softening position to HOLD until conditions stabilize."
            )
            evidence = [f"Accepted {challenge.from_market} critique", f"High Vol {vol:.1f}%"]
        else:
            new_pos = state.current_position
            conf = state.confidence
            reason = (
                f"Maintaining stance against {challenge.from_market}: Core signal intact with RSI {rsi:.1f}."
            )
            evidence = [f"Defended {state.current_position}", f"RSI {rsi:.1f}"]

        return new_pos, round(conf, 1), reason, evidence

    def final_stance(
        self, state: AgentState, board_messages: List[Message], candles: List[Candle]
    ) -> Tuple[Action, float, str, List[str]]:
        closes = [c.close for c in candles]
        vol = calculate_realized_volatility(closes)

        warnings = [m for m in board_messages if "volatility" in m.reason.lower() or "rotation" in m.reason.lower()]
        if len(warnings) >= 2 and state.current_position == Action.BUY and vol > 2.0:
            return (
                Action.HOLD,
                62.0,
                f"Consolidated debate consensus: Shifting to HOLD due to cross-market warnings on volatility ({vol:.1f}%).",
                [f"{len(warnings)} cross-market warnings", f"Vol {vol:.1f}%"],
            )

        return (
            state.current_position,
            state.confidence,
            f"Final position confirmed: {state.last_reason}",
            state.evidence,
        )
