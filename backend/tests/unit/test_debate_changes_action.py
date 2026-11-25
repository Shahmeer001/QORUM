"""
Debate mechanics: with hand-built data where the written rules apply, a
challenge -> reply must change the final action relative to silent-weighted.

US (target) says BUY with 14-bar volatility between the 2.4% reply threshold and
the 2.5% risk veto. CRYPTO disagrees (SELL) with volatility above the 2.0%
challenge threshold. Passing shows the plumbing works; it says nothing about how
often real data meets these thresholds.
"""
import math

from app.adapters.base import MarketDataAdapter
from app.agents.brains.rule_brain import RuleBrain
from app.agents.market_agent import MarketAgent
from app.board.memory_repo import MemoryBoardRepository
from app.domain.enums import Action, Mode, MsgType, RiskStatus, Role
from app.domain.models import Candle
from app.modes.dispatch import run_mode
from app.risk.risk_layer import RiskLayer


def _candles(drift: float, swing: float):
    price, out = 100.0, []
    for i in range(100):
        price *= math.exp(drift + (swing if i % 2 else -swing)) if i else 1.0
        out.append(Candle(timestamp=str(i), open=price, high=price, low=price, close=price, volume=1))
    return out


class _Stub(MarketDataAdapter):
    def __init__(self, candles):
        self.candles = candles

    def get_candles(self, symbol="", limit=100, date_str=None):
        return self.candles[-limit:]

    def get_latest(self, symbol=""):
        return self.candles[-1]


def _run(mode):
    board = MemoryBoardRepository()
    data = {"US": _candles(0.004, 0.0236), "CRYPTO": _candles(-0.001, 0.022)}
    agents = {
        m: MarketAgent(m, _Stub(c), board, role=Role.CHOSEN if m == "US" else Role.RELATED, brain=RuleBrain())
        for m, c in data.items()
    }
    for agent in agents.values():
        agent.knowledge = {}
    _, consensus, _, _ = run_mode(mode, agents, board, "s", "SPY", target_market="US")
    final = RiskLayer().evaluate(consensus, data["US"])
    return final, board.get_all("s")


def test_debate_changes_final_action_when_agents_disagree():
    (silent_action, silent_status, *_), _ = _run(Mode.SILENT_WEIGHTED)
    (debate_action, debate_status, *_), msgs = _run(Mode.DEBATE)

    opening = {m.from_market: m.position for m in msgs if m.msg_type == MsgType.RECOMMEND}
    assert opening == {"US": Action.BUY, "CRYPTO": Action.SELL}
    assert [(m.from_market, m.to_market) for m in msgs if m.msg_type == MsgType.CHALLENGE] == [("CRYPTO", "US")]
    assert silent_status == debate_status == RiskStatus.APPROVED  # not a risk-layer effect
    assert silent_action == Action.BUY
    assert debate_action == Action.HOLD
