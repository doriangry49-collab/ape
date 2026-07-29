from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Union


def _now_utc():
    return datetime.now(timezone.utc)


class PolicyDecision(str, Enum):
    BUILD = "BUILD"
    VALIDATE = "VALIDATE"
    WATCH = "WATCH"
    IGNORE = "IGNORE"
    BLOCKED = "BLOCKED"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PolicyGateResult:
    decision: PolicyDecision
    policy_code: str
    message: str
    rule_id: str


@dataclass(frozen=True)
class DecisionReport:
    decision_id: str
    research_id: str
    evidence_hash: str
    topic: str
    overall_score: int
    confidence: int
    decision: Union[PolicyDecision, str]
    policy: str
    vector_scores: Dict[str, int]
    rationale: List[str]
    next_step: str
    evidence_flags: Dict[str, Any] = field(default_factory=dict)
    provenance_chain: List[Any] = field(default_factory=list)
    reference_urls: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=_now_utc)

    def to_dict(self) -> dict:
        dec_str = self.decision.value if isinstance(self.decision, PolicyDecision) else str(self.decision)
        prov_list = []
        for p in self.provenance_chain:
            if is_dataclass(p) and not isinstance(p, type):
                prov_list.append(asdict(p))
            elif hasattr(p, "to_dict"):
                prov_list.append(p.to_dict())
            else:
                prov_list.append(p)

        return {
            "decision_id": self.decision_id,
            "research_id": self.research_id,
            "evidence_hash": self.evidence_hash,
            "topic": self.topic,
            "overall_score": self.overall_score,
            "confidence": self.confidence,
            "decision": dec_str,
            "policy": self.policy,
            "vector_scores": self.vector_scores,
            "rationale": self.rationale,
            "next_step": self.next_step,
            "evidence_flags": self.evidence_flags,
            "provenance_chain": prov_list,
            "reference_urls": self.reference_urls,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() + "Z",
        }

