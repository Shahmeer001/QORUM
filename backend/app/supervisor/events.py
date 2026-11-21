from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class SupervisorEventLog:
    round: int
    text: str
    event_type: str = "info"
