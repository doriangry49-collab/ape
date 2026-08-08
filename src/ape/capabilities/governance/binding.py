"""
Capability Binding Contract & Target Isolation — ORION-119.C & 119.5 Specification.
Decouples Capability ID from execution binding_id and enforces target_id isolation.
"""

from dataclasses import dataclass, field
from enum import Enum
import types
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Tuple

from ape.tools.definition import ToolPermission


class BindingType(str, Enum):
    """Execution primitive classification for capability bindings."""
    LLM = "llm"
    TOOL = "tool"
    COMPOSITE = "composite"


def _freeze(val: Any) -> Any:
    """Helper to convert mutable collections to immutable equivalents."""
    if isinstance(val, dict):
        return types.MappingProxyType({k: _freeze(v) for k, v in val.items()})
    elif isinstance(val, (list, tuple)):
        return tuple(_freeze(item) for item in val)
    elif isinstance(val, (set, frozenset)):
        return frozenset(_freeze(item) for item in val)
    return val


@dataclass(frozen=True)
class CapabilityBinding:
    """
    Governed binding pairing a capability identity to execution primitives.
    Deeply immutable structure enforcing target_id isolation.
    """
    binding_id: str
    capability_id: str
    version: str
    binding_type: BindingType
    target_id: str  # PromptID, ToolName, or GraphID (Target ISOLATED from callers)
    allowed_scopes: FrozenSet[str] = field(default_factory=frozenset)
    required_permissions: Tuple[ToolPermission, ...] = field(default_factory=tuple)
    evidence_policy: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "allowed_scopes", _freeze(self.allowed_scopes))
        object.__setattr__(self, "required_permissions", _freeze(self.required_permissions))
        object.__setattr__(self, "evidence_policy", _freeze(self.evidence_policy))
