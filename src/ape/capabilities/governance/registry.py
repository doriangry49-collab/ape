"""
Capability Registry & Lifecycle Contract — ORION-119.B & 119.1 Specification.
Manages versioned capability descriptors, lifecycle states (ACTIVE, DEPRECATED, REVOKED),
and deterministic version resolution with fail-closed safeguards.
"""

from enum import Enum
import re
from typing import Dict, List, Optional

from ape.capabilities.contracts import CapabilityError
from ape.capabilities.governance.descriptor import CapabilityDescriptor


class CapabilityLifecycleState(str, Enum):
    """Authoritative lifecycle state classification for capability descriptors."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    REVOKED = "revoked"


class UnresolvableVersionError(CapabilityError):
    """Raised when version constraint is invalid, unresolvable, or uses forbidden wildcards."""
    pass


class CapabilityRegistry:
    """Authoritative registry storing versioned CapabilityDescriptors and lifecycle states."""

    def __init__(self) -> None:
        self._capabilities: Dict[str, CapabilityDescriptor] = {}
        self._lifecycle: Dict[str, CapabilityLifecycleState] = {}

    def register(self, descriptor: CapabilityDescriptor) -> None:
        """Register a versioned CapabilityDescriptor in the registry."""
        q_id = descriptor.qualified_id
        if q_id in self._capabilities:
            raise CapabilityError(f"Capability descriptor '{q_id}' is already registered.")
        self._capabilities[q_id] = descriptor
        self._lifecycle[q_id] = CapabilityLifecycleState.ACTIVE

    def set_lifecycle_state(self, qualified_id: str, state: CapabilityLifecycleState) -> None:
        """Update lifecycle state for a registered capability version."""
        if qualified_id not in self._capabilities:
            raise CapabilityError(f"Capability '{qualified_id}' is not registered.")
        self._lifecycle[qualified_id] = state

    def get_lifecycle_state(self, qualified_id: str) -> CapabilityLifecycleState:
        """Return current lifecycle state for a registered capability version."""
        if qualified_id not in self._capabilities:
            raise CapabilityError(f"Capability '{qualified_id}' is not registered.")
        return self._lifecycle[qualified_id]

    def resolve_version(self, capability_id: str, version_constraint: Optional[str] = None) -> CapabilityDescriptor:
        """
        Deterministically resolve capability_id and version_constraint to a CapabilityDescriptor.
        Fails closed on 'latest', invalid syntax, or revoked versions.
        """
        # 1. Reject 'latest' wildcard or unparseable syntax
        if version_constraint is not None:
            v_str = version_constraint.strip().lower()
            if v_str in ("latest", "*", "any") or not re.match(r"^[\d\.\s<>=,^\~A-Za-z]+$", v_str):
                raise UnresolvableVersionError(
                    f"FAIL CLOSED: Forbidden or invalid version constraint '{version_constraint}' for capability '{capability_id}'."
                )

        # Find matching descriptors for capability_id
        matches = [d for q_id, d in self._capabilities.items() if d.capability_id == capability_id]
        if not matches:
            raise UnresolvableVersionError(f"No registered capability descriptor found for '{capability_id}'.")

        # 2. Exact version match
        if version_constraint:
            exact = [d for d in matches if d.version == version_constraint]
            if exact:
                target = exact[0]
                if self._lifecycle[target.qualified_id] == CapabilityLifecycleState.REVOKED:
                    raise UnresolvableVersionError(
                        f"FAIL CLOSED: Capability '{target.qualified_id}' is REVOKED and forbidden for new executions."
                    )
                return target

        # 3. Compatible / Highest stable fallback
        active_matches = [d for d in matches if self._lifecycle[d.qualified_id] == CapabilityLifecycleState.ACTIVE]
        if active_matches:
            # Sort by version tuple deterministically
            active_matches.sort(key=lambda d: [int(x) for x in d.version.split(".")], reverse=True)
            return active_matches[0]

        deprecated_matches = [d for d in matches if self._lifecycle[d.qualified_id] == CapabilityLifecycleState.DEPRECATED]
        if deprecated_matches:
            deprecated_matches.sort(key=lambda d: [int(x) for x in d.version.split(".")], reverse=True)
            return deprecated_matches[0]

        raise UnresolvableVersionError(
            f"FAIL CLOSED: All registered capability versions for '{capability_id}' are REVOKED or unresolvable."
        )
