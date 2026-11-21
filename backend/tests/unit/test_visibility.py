from app.board.visibility import filter_visible_messages
from app.domain.enums import Action, MsgType
from app.domain.models import Message


def test_visibility_closed_markets_visible_open_markets_hidden():
    open_status = {"CRYPTO": True, "GOLD": False, "US": False}
    msgs = [
        Message(
            id="1", session_id="s1", round=0, from_market="GOLD", to_market="BOARD",
            msg_type=MsgType.RECOMMEND, position=Action.BUY, reason="Gold closed",
        ),
        Message(
            id="2", session_id="s1", round=0, from_market="CRYPTO", to_market="BOARD",
            msg_type=MsgType.RECOMMEND, position=Action.SELL, reason="Crypto open",
        ),
    ]

    filtered = filter_visible_messages(msgs, open_status)
    assert filtered[0].is_visible is True
    assert filtered[1].is_visible is False
