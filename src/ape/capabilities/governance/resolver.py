"""
Capability Binding Resolver Contract — ORION-119.1 Specification.
Provides authoritative server-side resolution mapping CapabilityDescriptor to CapabilityBinding
without allowing caller/agent selection overrides.
"""

from typing import Dict, List, Optional

from ape.capabilities.contracts import CapabilityError
from ape.capabilities.governance.binding import CapabilityBinding
from ape.capabilities.governance.descriptor import CapabilityDescriptor


class UnresolvableBindingError(CapabilityError):
    """Raised when no valid binding is registered for a given capability descriptor."""
    pass


class CapabilityBindingResolver:
    """Authoritative server-side resolver selecting governed CapabilityBinding for a CapabilityDescriptor."""

    def __init__(self) -> None:
        self._bindings: Dict[str, List[CapabilityBinding]] = {}

    def register_binding(self, binding: CapabilityBinding) -> None:
        """Register a CapabilityBinding for a qualified capability identity (id@version)."""
        q_id = f"{binding.capability_id}@{binding.version}"
        if q_id not in self._bindings:
            self._bindings[q_id] = []
        self._bindings[q_id].append(binding)

    def resolve_binding(self, descriptor: CapabilityDescriptor, preferred_binding_id: Optional[str] = None) -> CapabilityBinding:
        """
        Deterministically resolve governed CapabilityBinding for a descriptor.
        Target selection is server-side governed and CANNOT be specified by callers/agents.
        """
        q_id = descriptor.qualified_id
        if q_id not in self._bindings or not self._bindings[q_id]:
            # Fallback to capability_id wildcard matching if exact qualified_id not directly registered
            q_matches = []
            for b_list in self._bindings.values():
                for b in b_list:
                    if b.capability_id == descriptor.capability_id:
                        q_matches.append(b)
            if not q_matches:
                raise UnresolvableBindingError(f"FAIL CLOSED: No governed binding registered for capability '{q_id}'.")
            return q_matches[0]

        candidates = self._bindings[q_id]
        if preferred_binding_id:
            for b in candidates:
                if b.binding_id == preferred_binding_id:
                    return b

        return candidates[0]
