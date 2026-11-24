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
    SILENT = "silent"  # legacy alias; behaves as silent-weighted
    SILENT_UNWEIGHTED = "silent_unweighted"
    SILENT_WEIGHTED = "silent_weighted"
    DEBATE = "debate"


class Role(str, Enum):
    CHOSEN = "CHOSEN"
    RELATED = "RELATED"


class MarketId(str, Enum):
    CRYPTO = "CRYPTO"
    US = "US"
    PSX = "PSX"
    FOREX = "FOREX"
    GOLD = "GOLD"


class RiskStatus(str, Enum):
    APPROVED = "Approved"
    OVERRIDDEN = "Overridden"
    REJECTED = "Rejected"
    QUORUM_NOT_MET = "Quorum Not Met"


class DataStatus(str, Enum):
    VALID = "VALID"
    NO_DATA = "NO_DATA"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
