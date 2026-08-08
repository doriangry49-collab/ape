"""
Capability Identity & Semantic Versioning Contract — ORION-119.A Specification.
Provides deeply immutable CapabilityDescriptor with versioning (MAJOR.MINOR.PATCH) and risk protections.
"""

from dataclasses import dataclass, field
from enum import Enum
import types
from typing import Any, Dict, Mapping, Optional, Tuple

from ape.tools.definition import RiskLevel


class CapabilityType(str, Enum):
    """Classification of capability type."""
    ATOMIC = "atomic"
    COMPOSITE = "composite"


def _freeze_dict(d: Any) -> Any:
    """Recursively freeze dictionary into immutable MappingProxyType."""
    if isinstance(d, dict):
        return types.MappingProxyType({k: _freeze_dict(v) for k, v in d.items()})
    elif isinstance(d, list):
        return tuple(_freeze_dict(item) for item in d)
    elif isinstance(d, set):
        return frozenset(_freeze_dict(item) for item in d)
    return d


@dataclass(frozen=True)
class CapabilityDescriptor:
    """
    Deeply immutable versioned descriptor representing a governed capability intent.
    Enforces deep immutability across nested mappings, lists, and metadata structures.
    """
    capability_id: str
    version: str  # Semantic versioning (MAJOR.MINOR.PATCH)
    category: str
    description: str
    capability_type: CapabilityType = CapabilityType.ATOMIC
    input_schema: Mapping[str, Any] = field(default_factory=dict)
    output_schema: Mapping[str, Any] = field(default_factory=dict)
    risk_tier: RiskLevel = RiskLevel.LOW
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Enforce deep immutability for nested structures
        object.__setattr__(self, "input_schema", _freeze_dict(dict(self.input_schema)))
        object.__setattr__(self, "output_schema", _freeze_dict(dict(self.output_schema)))
        object.__setattr__(self, "metadata", _freeze_dict(dict(self.metadata)))

    @property
    def qualified_id(self) -> str:
        """Return fully qualified versioned capability identity (e.g. 'engineering.code.generate@1.0.0')."""
        return f"{self.capability_id}@{self.version}"
