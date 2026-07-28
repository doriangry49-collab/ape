from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ResearchReport:
    topic: str
    target_audience: list[str]
    competitors: list[str]
    pain_points: list[str]
    market_signals: list[str]
    risks: list[str]
    confidence: float
    sources: list[str]
    discussions: list[dict]
    suggested_mvp: list[str]
    timestamp: datetime
    next_recommended_action: str
    metadata: dict[str, str]

