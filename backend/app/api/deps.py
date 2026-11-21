from __future__ import annotations

from typing import Generator
from sqlalchemy.orm import Session
from app.db.connection import get_db

# Re-export db dependency
__all__ = ["get_db"]
