from datetime import datetime, timezone
import pytest

from app.adapters.binance_btc import BinanceBTCAdapter
from app.adapters.us_spy import USMarketAdapter
from app.board.memory_repo import MemoryBoardRepository
from app.board.visibility import (
    filter_visible_data,
    is_candle_visible,
    is_message_visible_to_reader,
)
from app.config.settings import get_us_close_utc
from app.domain.enums import Action, MsgType
from app.domain.models import Candle, Message


def test_candle_closes_after_decision_time_never_returned():
    """Test 1: A candle that closes after the decision time is never returned."""
    decision_time = datetime(2026, 11, 10, 21, 0, 0, tzinfo=timezone.utc)

    candle_before = Candle(
        timestamp="2026-11-10T20:55:00Z", open=100, high=101, low=99, close=100.5, volume=100
    )
    candle_exact = Candle(
        timestamp="2026-11-10T21:00:00Z", open=100.5, high=102, low=100, close=101.5, volume=100
    )
    candle_after = Candle(
        timestamp="2026-11-10T21:05:00Z", open=101.5, high=103, low=101, close=102.5, volume=100
    )

    candles = [candle_before, candle_exact, candle_after]
    _, visible_candles = filter_visible_data(
        reader_market="GOLD",
        current_round=0,
        decision_time_utc=decision_time,
        candles=candles,
    )

    assert len(visible_candles) == 2
    assert candle_after not in visible_candles
    assert all(is_candle_visible(c, decision_time) for c in visible_candles)


def test_message_from_current_round_invisible_to_other_agent():
    """Test 2: A message from the current round is invisible to the other agent."""
    m_r0_other = Message(
        id="m1", session="s1", round=0, sender="US", recipient="BOARD",
        type=MsgType.RECOMMEND, position=Action.BUY, reason="R0 US"
    )
    m_r1_other = Message(
        id="m2", session="s1", round=1, sender="CRYPTO", recipient="GOLD",
        type=MsgType.CHALLENGE, position=Action.SELL, reason="R1 Crypto"
    )
    m_r1_own = Message(
        id="m3", session="s1", round=1, sender="GOLD", recipient="CRYPTO",
        type=MsgType.REPLY, position=Action.HOLD, reason="R1 Gold own reply"
    )

    # Reader is GOLD in round 1
    # Should see R0 from US, and its own R1 message, but NOT R1 from CRYPTO
    assert is_message_visible_to_reader(m_r0_other, reader_market="GOLD", current_round=1) is True
    assert is_message_visible_to_reader(m_r1_own, reader_market="GOLD", current_round=1) is True
    assert is_message_visible_to_reader(m_r1_other, reader_market="GOLD", current_round=1) is False

    visible_msgs, _ = filter_visible_data(
        reader_market="GOLD",
        current_round=1,
        decision_time_utc=datetime.now(timezone.utc),
        messages=[m_r0_other, m_r1_other, m_r1_own],
    )
    assert m_r0_other in visible_msgs
    assert m_r1_own in visible_msgs
    assert m_r1_other not in visible_msgs


def test_weekends_us_adapter_no_new_candle_btc_works():
    """Test 3: Weekends: the US adapter has no new candle, and BTC still works."""
    saturday = "2026-11-14"
    sunday = "2026-11-15"
    monday = "2026-11-16"

    us_adapter = USMarketAdapter()
    btc_adapter = BinanceBTCAdapter()

    # US market is closed on weekends
    assert len(us_adapter.get_candles(date_str=saturday)) == 0
    assert len(us_adapter.get_candles(date_str=sunday)) == 0
    assert len(us_adapter.get_candles(date_str=monday)) > 0

    # BTC trades 24/7/365 (still honours the decision-date cutoff)
    btc_candles = btc_adapter.get_candles(date_str=monday, limit=10)
    assert len(btc_candles) > 0


def test_us_close_shifts_across_daylight_saving():
    """Test 4: The US close shifts correctly across a daylight-saving change."""
    # US Eastern Time:
    # Summer (EDT, UTC-4): 4:00 PM local is 20:00 UTC
    summer_day = "2026-06-15"
    summer_close_utc = get_us_close_utc(summer_day)
    assert summer_close_utc.hour == 20
    assert summer_close_utc.minute == 0

    # Winter (EST, UTC-5): 4:00 PM local is 21:00 UTC
    winter_day = "2026-12-15"
    winter_close_utc = get_us_close_utc(winter_day)
    assert winter_close_utc.hour == 21
    assert winter_close_utc.minute == 0


def test_memory_repo_rejects_edit_or_delete():
    """Test 5: The memory repo rejects any attempt to edit or delete a message."""
    repo = MemoryBoardRepository()
    msg = Message(
        id="m100", session="s1", round=0, sender="GOLD", recipient="BOARD",
        type=MsgType.RECOMMEND, position=Action.BUY, reason="Testing immutability"
    )
    repo.add_message(msg)

    # 1. Calling update_message or delete_message raises PermissionError
    with pytest.raises(PermissionError):
        repo.update_message(msg)

    with pytest.raises(PermissionError):
        repo.delete_message("m100")

    # 2. Modifying returned message copy does not alter stored message
    retrieved = repo.get_messages("s1")
    retrieved[0].reason = "Tampered reason"
    retrieved_again = repo.get_messages("s1")
    assert retrieved_again[0].reason == "Testing immutability"
