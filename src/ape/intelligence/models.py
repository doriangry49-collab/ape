from __future__ import annotations

from dataclasses import dataclass, field
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
    request_context: Optional[str] = None
    retrieval_timestamp: Optional[datetime] = None

@dataclass(frozen=True)
class PainPoint:
    domain: str
    description: str
    frequency_signal: Union[int, UnknownType]
    payment_signal: Union[bool, int, UnknownType]
    ai_solvable: Union[bool, UnknownType]

@dataclass(frozen=True)
class BusinessEvidence:
    search_intent_observation: Union[bool, UnknownType]
    pain_observation: Union[bool, UnknownType]
    manual_work_observation: Union[bool, UnknownType]
    pricing_observation: Union[bool, UnknownType]
    entity_observation: Union[bool, UnknownType]
    competition_observation: Union[bool, UnknownType]
    provenance: EvidenceProvenance
    ai_solvability: UnknownType = UNKNOWN

    @classmethod
    def all_unknown(cls) -> "BusinessEvidence":
        return cls(
            search_intent_observation=UNKNOWN,
            pain_observation=UNKNOWN,
            manual_work_observation=UNKNOWN,
            pricing_observation=UNKNOWN,
            entity_observation=UNKNOWN,
            competition_observation=UNKNOWN,
            ai_solvability=UNKNOWN,
            provenance=EvidenceProvenance(source_adapter="synthetic", raw_observation="synthetic_all_unknown")
        )

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
    business_evidence: list[BusinessEvidence] = field(default_factory=list)
    is_hypothesis: bool = False
