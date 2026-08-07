"""
Venture Outcome Domain Entity — ORION-105 Specification.
Tracks operational venture outcome state (RUNNING, VALIDATED, REJECTED, SCALING).
"""

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any, Dict, List


class OutcomeStatus(str, Enum):
    """Operational status of a venture outcome."""
    RUNNING = "RUNNING"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    SCALING = "SCALING"


@dataclass
class VentureOutcome:
    """Outcome packet feeding organizational learning."""
    outcome_id: str
    goal_id: str
    product_id: str
    status: OutcomeStatus = OutcomeStatus.RUNNING
    findings: List[str] = field(default_factory=list)
    recorded_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize VentureOutcome into dictionary payload."""
        return {
            "outcome_id": self.outcome_id,
            "goal_id": self.goal_id,
            "product_id": self.product_id,
            "status": self.status.value,
            "findings_count": len(self.findings),
            "recorded_at": self.recorded_at,
        }
