"""
Business Unit Registry — RFC-022 / Phase B1 Specification.
Manages and resolves Business Units across organizational domains.
"""

from typing import Dict, List, Optional
from ape.business.contracts import BusinessUnit


class BusinessUnitRegistry:
    """Registry engine tracking organizational Business Units."""

    def __init__(self) -> None:
        self._units: Dict[str, BusinessUnit] = {}

    def register_unit(self, unit: BusinessUnit) -> None:
        """Register a Business Unit."""
        key = unit.name.strip().lower()
        self._units[key] = unit

    def get_unit(self, name: str) -> Optional[BusinessUnit]:
        """Fetch Business Unit by name."""
        return self._units.get(name.strip().lower())

    def list_all_units(self) -> List[BusinessUnit]:
        """Return list of all registered Business Units."""
        return list(self._units.values())


# Global default business unit registry instance
default_business_unit_registry = BusinessUnitRegistry()


def get_default_business_unit_registry() -> BusinessUnitRegistry:
    """Returns global default business unit registry instance."""
    return default_business_unit_registry
