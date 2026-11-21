from __future__ import annotations

from enum import Enum


class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    ABSTAIN = "ABSTAIN"


class MsgType(str, Enum):
    RECOMMEND = "RECOMMEND"
    CHALLENGE = "CHALLENGE"
    REPLY = "REPLY"
    FINAL = "FINAL"


class Mode(str, Enum):
    SINGLE = "single"
    SILENT = "silent"
    DEBATE = "debate"


class Role(str, Enum):
    CHOSEN = "CHOSEN"
    RELATED = "RELATED"


class RiskStatus(str, Enum):
    APPROVED = "Approved"
    OVERRIDDEN = "Overridden"
    REJECTED = "Rejected"
