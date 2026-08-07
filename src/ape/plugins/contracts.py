"""
Plugin SDK Constitutional Contracts & Protocol Interfaces — RFC-022 / PR-P1 Specification.
Defines ApePlugin protocol interface for third-party extensions.
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ApePlugin(Protocol):
    """Constitutional Protocol contract that all APE plugins must implement."""

    name: str
    version: str
    api_version: str

    def register(self, registry: Any) -> None:
        """Register extensions into ExtensionRegistry."""
        ...
