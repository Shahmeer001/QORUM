"""
Trade Simulation Engine.
Computes deterministic execution trades and equity curve following a session's final action.
All numbers derive strictly from actual candle prices and configured friction (commission + slippage).
No hard-coded curves, points, or mock PnL values.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml

from app.config.settings import BASE_DIR, INITIAL_CAPITAL
from app.domain.enums import Action
from app.domain.models import Candle, EquityPoint, Trade


@dataclass
class MarketFriction:
    commission: float  # e.g. 0.0005 = 0.05%
    slippage: float    # e.g. 0.0002 = 0.02%


_FRICTION_CACHE: Optional[Dict[str, MarketFriction]] = None


def get_market_friction(market: str) -> MarketFriction:
    """Loads commission and slippage config from markets.yaml with fail-safe defaults."""
    global _FRICTION_CACHE
    if _FRICTION_CACHE is None:
        cache: Dict[str, MarketFriction] = {}
        config_path = BASE_DIR / "app" / "config" / "markets.yaml"
        if config_path.exists():
            try:
                data = yaml.safe_load(config_path.read_text(encoding="utf-8")).get("markets", {})
                for m_id, m_cfg in data.items():
                    cache[m_id.upper()] = MarketFriction(
                        commission=float(m_cfg.get("commission", 0.0005)),
                        slippage=float(m_cfg.get("slippage", 0.0002)),
                    )
            except Exception:
                pass
        _FRICTION_CACHE = cache

    default_frictions = {
        "US": MarketFriction(commission=0.0005, slippage=0.0002),
        "CRYPTO": MarketFriction(commission=0.0010, slippage=0.0005),
    }
    return _FRICTION_CACHE.get(market.upper(), default_frictions.get(market.upper(), MarketFriction(commission=0.0005, slippage=0.0002)))


def execute_fill(
    action: Action,
    raw_price: float,
    friction: MarketFriction,
    is_entry: bool,
    is_short: bool = False,
) -> float:
    """
    Applies adverse slippage to execute fill:
    - Long entry: pays higher price (1 + slippage)
    - Long exit: receives lower price (1 - slippage)
    - Short entry: receives lower price (1 - slippage)
    - Short exit: pays higher price (1 + slippage)
    """
    if is_short:
        if is_entry:
            return raw_price * (1.0 - friction.slippage)
        else:
            return raw_price * (1.0 + friction.slippage)
    else:
        if is_entry:
            return raw_price * (1.0 + friction.slippage)
        else:
            return raw_price * (1.0 - friction.slippage)


def calculate_trade_pnl(
    entry_fill: float,
    exit_fill: float,
    units: float,
    friction: MarketFriction,
    is_short: bool = False,
) -> Tuple[float, float, float]:
    """
    Computes exact trade PnL incorporating slippage-adjusted fills and commissions.
    Returns (net_pnl, total_commission, gross_pnl).
    """
    entry_notional = units * entry_fill
    exit_notional = units * exit_fill
    entry_comm = entry_notional * friction.commission
    exit_comm = exit_notional * friction.commission
    total_comm = entry_comm + exit_comm

    if is_short:
        gross_pnl = units * (entry_fill - exit_fill)
    else:
        gross_pnl = units * (exit_fill - entry_fill)

    net_pnl = gross_pnl - total_comm
    return net_pnl, total_comm, gross_pnl


def simulate_trades(
    final_action: Action,
    target_market: str,
    candles: List[Candle],
    initial_capital: float = INITIAL_CAPITAL,
    allow_short: bool = False,
) -> Tuple[List[Trade], List[EquityPoint]]:
    """
    Simulates performance on real candle series.
    All equity values and trade outcomes are computed dynamically from actual prices.
    """
    if not candles:
        return [], [EquityPoint(t="0", v=round(initial_capital, 2))]

    # Default flat line if insufficient history or non-position action (HOLD/ABSTAIN)
    if len(candles) < 2 or final_action in (Action.HOLD, Action.ABSTAIN):
        equity = [
            EquityPoint(t=c.timestamp.split()[0] if " " in c.timestamp else c.timestamp, v=round(initial_capital, 2))
            for c in candles
        ]
        return [], equity

    # If action is SELL and shorting is disabled, stance is flat (cash protected)
    if final_action == Action.SELL and not allow_short:
        equity = [
            EquityPoint(t=c.timestamp.split()[0] if " " in c.timestamp else c.timestamp, v=round(initial_capital, 2))
            for c in candles
        ]
        return [], equity

    friction = get_market_friction(target_market)
    is_short = (final_action == Action.SELL)

    entry_raw = candles[0].open
    entry_fill = execute_fill(final_action, entry_raw, friction, is_entry=True, is_short=is_short)
    if entry_fill <= 0:
        return [], [EquityPoint(t="0", v=round(initial_capital, 2))]

    units = initial_capital / entry_fill
    entry_comm = units * entry_fill * friction.commission
    cash = initial_capital - (units * entry_fill if not is_short else 0.0) - entry_comm

    equity: List[EquityPoint] = []
    for c in candles:
        if is_short:
            eq = initial_capital + units * (entry_fill - c.close) - entry_comm
        else:
            eq = cash + units * c.close
        equity.append(
            EquityPoint(
                t=c.timestamp.split()[0] if " " in c.timestamp else c.timestamp,
                v=round(eq, 2),
            )
        )

    exit_raw = candles[-1].close
    exit_fill = execute_fill(final_action, exit_raw, friction, is_entry=False, is_short=is_short)
    net_pnl, total_comm, _ = calculate_trade_pnl(entry_fill, exit_fill, units, friction, is_short=is_short)

    # Reflect realized exit friction on final equity point
    equity[-1] = EquityPoint(
        t=equity[-1].t,
        v=round(initial_capital + net_pnl, 2),
    )

    trades = [
        Trade(
            entry=candles[0].timestamp,
            exit=candles[-1].timestamp,
            side=final_action,
            market=target_market,
            pnl=round(net_pnl, 2),
            note=(
                f"Fill {entry_fill:.2f} -> Exit {exit_fill:.2f} "
                f"({'Short' if is_short else 'Long'}, friction: ${total_comm:.2f})"
            ),
        )
    ]

    return trades, equity
