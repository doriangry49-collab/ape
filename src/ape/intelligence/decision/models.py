from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List


def _now_utc():
    return datetime.now(timezone.utc)

@dataclass(frozen=True)
class DecisionReport:
    decision_id: str
    research_id: str
    evidence_hash: str
    topic: str
    overall_score: int
    confidence: int
    decision: str
    policy: str
    vector_scores: Dict[str, int]
    rationale: List[str]
    next_step: str
    metadata: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=_now_utc)

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "research_id": self.research_id,
            "evidence_hash": self.evidence_hash,
            "topic": self.topic,
            "overall_score": self.overall_score,
            "confidence": self.confidence,
            "decision": self.decision,
            "policy": self.policy,
            "vector_scores": self.vector_scores,
            "rationale": self.rationale,
            "next_step": self.next_step,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() + "Z"
        }
