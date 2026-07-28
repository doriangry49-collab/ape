from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional, Union

# Define UNKNOWN state
UNKNOWN = "UNKNOWN"
UnknownType = Literal["UNKNOWN"]

@dataclass(frozen=True)
class EvidenceProvenance:
    source_adapter: str
    raw_observation: str
    reference_url: Optional[str] = None

@dataclass(frozen=True)
class PainPoint:
    domain: str
    description: str
    frequency_signal: Union[int, UnknownType]
    payment_signal: Union[bool, int, UnknownType]
    ai_solvable: Union[bool, UnknownType]

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
    # Business discovery extensions
    pain_point: Optional[PainPoint] = None
    provenance: Optional[EvidenceProvenance] = None
    is_hypothesis: bool = False
