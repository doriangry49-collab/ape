"""
Business Operating System Contracts — RFC-022 / Phase B1 Specification.
Defines BusinessUnit Protocol interface and UnitReport schemas for AI Business Units.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol, runtime_checkable


@dataclass
class UnitReport:
    """Standardized report returned by a Business Unit execution cycle."""
    unit_name: str
    objectives_met: List[str] = field(default_factory=list)
    kpis_calculated: Dict[str, float] = field(default_factory=dict)
    artifacts_produced: List[str] = field(default_factory=list)
    status: str = "COMPLETED"  # COMPLETED, IN_PROGRESS, FAILED
    findings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unit_name": self.unit_name,
            "objectives_met": self.objectives_met,
            "kpis_calculated": self.kpis_calculated,
            "artifacts_produced": self.artifacts_produced,
            "status": self.status,
            "findings": self.findings,
        }


@runtime_checkable
class BusinessUnit(Protocol):
    """Constitutional Protocol contract for AI Business Units."""

    name: str
    objectives: List[str]
    kpis: List[str]

    def plan(self, strategic_objective: str) -> Dict[str, Any]:
        """Formulate unit-level execution plan for a strategic objective."""
        ...

    def execute(self, workspace_context: Any) -> UnitReport:
        """Execute unit operations using allocated Fabric Agent workforce."""
        ...

    def review(self) -> Dict[str, Any]:
        """Perform self-review and audit unit KPIs."""
        ...

    def report(self) -> UnitReport:
        """Return latest UnitReport."""
        ...
