"""
Base Business Unit Implementation — RFC-022 / Phase B1 Specification.
"""

from typing import Any, Dict, List
from ape.business.contracts import BusinessUnit, UnitReport


class BaseBusinessUnit:
    """Abstract base class for AI Business Units."""

    name: str = "base_unit"
    objectives: List[str] = []
    kpis: List[str] = []

    def __init__(self, name: str, objectives: List[str], kpis: List[str]) -> None:
        self.name = name
        self.objectives = objectives
        self.kpis = kpis

    def plan(self, strategic_objective: str) -> Dict[str, Any]:
        return {
            "unit": self.name,
            "objective": strategic_objective,
            "tasks": [f"Execute operation for '{strategic_objective}'"],
        }

    def execute(self, workspace_context: Any) -> UnitReport:
        return UnitReport(
            unit_name=self.name,
            objectives_met=self.objectives,
            kpis_calculated={k: 100.0 for k in self.kpis},
            status="COMPLETED",
        )

    def review(self) -> Dict[str, Any]:
        return {"unit": self.name, "status": "VERIFIED"}

    def report(self) -> UnitReport:
        return UnitReport(unit_name=self.name, status="COMPLETED")
