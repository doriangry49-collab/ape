"""
Executive Decision Layer — RFC-022 / Phase B3 Specification.
Models CEOAgent, CTOAgent, and ExecutiveBoard to delegate strategic directives down to Business Units.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from ape.business.contracts import UnitReport
from ape.business.registry import BusinessUnitRegistry, get_default_business_unit_registry


@dataclass
class ExecutiveDirective:
    """Strategic directive issued by Executive Board."""
    objective: str
    target_kpi: str
    priority: str = "HIGH"  # CRITICAL, HIGH, MEDIUM


class ExecutiveBoard:
    """Executive Decision Layer orchestrating Business Units for strategic objectives."""

    def __init__(self, registry: Optional[BusinessUnitRegistry] = None) -> None:
        self.registry = registry or get_default_business_unit_registry()
        self.directives_history: List[ExecutiveDirective] = []

    def issue_directive(self, objective: str, target_kpi: str = "engineering_velocity") -> ExecutiveDirective:
        """Formulate and log strategic directive."""
        directive = ExecutiveDirective(objective=objective, target_kpi=target_kpi)
        self.directives_history.append(directive)
        return directive

    def execute_directive(self, directive: ExecutiveDirective, workspace_context: Any) -> Dict[str, Any]:
        """Delegate executive directive down to all registered Business Units."""
        units = self.registry.list_all_units()
        unit_reports: List[UnitReport] = []

        for unit in units:
            unit.plan(directive.objective)
            rep = unit.execute(workspace_context)
            unit_reports.append(rep)

        return {
            "directive": directive.objective,
            "units_executed": len(unit_reports),
            "status": "APPROVED",
        }
