"""APE Calibration Framework — Schema Contracts & Validation Engine.

Provides types, contracts, and temporal leakage validators for historical calibration opportunities.
Isolated from production execution. Zero code modifications to core pipeline.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class PolicyDecisionEnum(str, Enum):
    """Constitutional Policy Decision Vocabulary aligned strictly with APE Decision Engine."""
    BUILD = "BUILD"
    VALIDATE_WITH_USERS = "VALIDATE_WITH_USERS"
    WAIT_FOR_SIGNAL = "WAIT_FOR_SIGNAL"


class MarketOutcomeEnum(str, Enum):
    """Categorical market outcome classifications for historical ground truth."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"


class TemporalLeakageError(ValueError):
    """Raised when evidence snapshot timestamp post-dates the decision timestamp."""
    pass


class ProvenanceValidationError(ValueError):
    """Raised when an opportunity record lacks valid evidence provenance or hashes."""
    pass


@dataclass
class EvidenceSnapshot:
    """Represents an isolated, immutable snapshot of evidence available at a given time."""
    source: str
    source_type: str
    observed_at: str
    available_at: str
    reference: str
    content_hash: str
    raw_observation: str

    def validate_timestamps(self, decision_timestamp_str: str) -> None:
        """Enforce Temporal Replay Boundary: available_at <= decision_timestamp."""
        available_dt = datetime.fromisoformat(self.available_at.replace("Z", "+00:00"))
        decision_dt = datetime.fromisoformat(decision_timestamp_str.replace("Z", "+00:00"))

        if available_dt > decision_dt:
            raise TemporalLeakageError(
                f"Temporal Leakage Detected! Evidence '{self.reference}' available at {self.available_at} "
                f"is after decision timestamp {decision_timestamp_str}."
            )

    def validate_provenance(self) -> None:
        """Verify evidence snapshot contains non-empty source and reference metadata."""
        if not self.source or not self.reference or not self.content_hash:
            raise ProvenanceValidationError(
                f"Evidence snapshot '{self.source}' missing required provenance metadata (reference/content_hash)."
            )


@dataclass
class OutcomeRecord:
    """Represents verified ground truth outcome data for a historical opportunity."""
    actual_market_outcome: MarketOutcomeEnum
    outcome_observed_at: str
    outcome_source: str
    outcome_confidence: float
    provenance_details: str

    def validate(self) -> None:
        if not (0.0 <= self.outcome_confidence <= 1.0):
            raise ValueError(f"Outcome confidence must be between 0.0 and 1.0, got {self.outcome_confidence}")
        if not self.outcome_source or not self.provenance_details:
            raise ProvenanceValidationError("Outcome record must contain non-empty source and provenance details.")


@dataclass
class CalibrationOpportunity:
    """Represents a single historical calibration opportunity record."""
    opportunity_id: str
    prompt_topic: str
    decision_timestamp: str
    human_expert_decision: PolicyDecisionEnum
    evidence_snapshots: List[EvidenceSnapshot]
    outcome: OutcomeRecord
    inclusion_rationale: str
    ape_decision: Optional[PolicyDecisionEnum] = None

    def validate(self) -> None:
        """Perform comprehensive validation: temporal boundary, provenance, and outcome integrity."""
        if not self.opportunity_id or not self.prompt_topic:
            raise ProvenanceValidationError("Opportunity record must contain opportunity_id and prompt_topic.")

        if not self.evidence_snapshots:
            raise ProvenanceValidationError(
                f"Opportunity '{self.opportunity_id}' has zero evidence snapshots! Unbacked records prohibited."
            )

        for snapshot in self.evidence_snapshots:
            snapshot.validate_provenance()
            snapshot.validate_timestamps(self.decision_timestamp)

        self.outcome.validate()
