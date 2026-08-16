"""
Quality OS Contracts & Interfaces — RFC-022 Specification.
Defines language-agnostic Validator Protocol, ValidationResult, ValidationContext, and QualityReport data structures.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol


class ValidationStatus(str, Enum):
    """Status outcome of a validator execution."""
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass
class ValidationContext:
    """Context provided to validators during Quality OS evaluation."""
    project_root: Path
    topic_slug: str
    deliverables: list[str]
    dry_run: bool = False
    quality_profile: str = "strict"
    metadata: dict[str, Any] = field(default_factory=dict)
    # Optional: explicit src root for src/-layout packages.
    # When set, validators inject this into PYTHONPATH for subprocess calls.
    # When None, validators auto-detect by checking project_root/src/.
    src_root: Path | None = None


@dataclass
class ValidationResult:
    """Standardized output produced by a Validator."""
    validator_name: str
    status: ValidationStatus
    score: float  # 0.0 to 100.0
    duration_ms: float
    is_critical: bool = True
    weight: float = 1.0
    findings: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    logs: dict[str, str] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "validator_name": self.validator_name,
            "status": self.status.value,
            "score": round(self.score, 2),
            "duration_ms": round(self.duration_ms, 2),
            "is_critical": self.is_critical,
            "weight": self.weight,
            "findings": self.findings,
            "warnings": self.warnings,
            "errors": self.errors,
            "artifacts": self.artifacts,
            "logs": self.logs,
            "metrics": self.metrics,
        }


class Validator(Protocol):
    """Language-agnostic Protocol interface for Quality OS Validators."""

    @property
    def name(self) -> str:
        ...

    @property
    def is_critical(self) -> bool:
        ...

    @property
    def weight(self) -> float:
        ...

    def validate(self, context: ValidationContext) -> ValidationResult:
        ...


@dataclass
class QualityReport:
    """Aggregated quality report for a set of validated deliverables."""
    overall_score: float  # Weighted score 0.0 to 100.0
    quality_audit_passed: bool
    results: list[ValidationResult] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    evidence_manifest: dict[str, Any] = field(default_factory=dict)
    reports: dict[str, str] = field(default_factory=dict)
    release_confidence: float = 100.0
    risk_level: str = "LOW"
    capability_coverage: dict[str, Any] = field(default_factory=dict)
    confidence_reasons: list[str] = field(default_factory=list)
    quality_profile: str = "standard"
    score_weights: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 2),
            "quality_audit_passed": self.quality_audit_passed,
            "release_confidence": round(self.release_confidence, 2),
            "risk_level": self.risk_level,
            "quality_profile": self.quality_profile,
            "score_weights": self.score_weights,
            "confidence_reasons": self.confidence_reasons,
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary,
            "capability_coverage": self.capability_coverage,
            "evidence_manifest": self.evidence_manifest,
            "reports": self.reports,
        }
