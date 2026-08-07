"""
Replay Engine Data Contracts & Models — RFC-022 / PR-G1 Specification.
Defines ReplayReport and ReplayResult structures.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ReplayReport:
    """Structured report produced by ReplayEngine verification."""
    build_id: str
    topic_slug: str
    quality_profile: str
    is_reproducible: bool
    confidence_delta: float
    original_confidence: float
    replay_confidence: float
    merkle_root_match: bool
    artifact_hash_match: bool
    runtime_passed: bool
    delta_reasons: list[str] = field(default_factory=list)
    artifacts_verified: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "build_id": self.build_id,
            "topic_slug": self.topic_slug,
            "quality_profile": self.quality_profile,
            "is_reproducible": self.is_reproducible,
            "confidence_delta": round(self.confidence_delta, 4),
            "original_confidence": round(self.original_confidence, 2),
            "replay_confidence": round(self.replay_confidence, 2),
            "merkle_root_match": self.merkle_root_match,
            "artifact_hash_match": self.artifact_hash_match,
            "runtime_passed": self.runtime_passed,
            "delta_reasons": self.delta_reasons,
            "artifacts_verified": self.artifacts_verified,
            "summary": self.summary,
        }
