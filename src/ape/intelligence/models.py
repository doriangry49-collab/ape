from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Opportunity:
    title: str
    description: str
    url: str
    source: str
    score: int
    confidence: float
    published_at: datetime
    tags: list[str]
