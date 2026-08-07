"""
Extension Points Registry — RFC-022 / PR-P2 Specification.
Provides ExtensionPoint Enum and ExtensionRegistry for dynamic plugin extension tracking.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from ape.plugins.exceptions import DuplicatePluginError


class ExtensionPoint(str, Enum):
    """The 8 constitutional extension points supported by APE Plugin SDK."""
    VALIDATOR = "validator"
    RUNTIME_PACK = "runtime_pack"
    RESEARCH_PROVIDER = "research_provider"
    POLICY_PROVIDER = "policy_provider"
    DASHBOARD_WIDGET = "dashboard_widget"
    CLI_COMMAND = "cli_command"
    QUALITY_PROFILE = "quality_profile"
    REPLAY_PROVIDER = "replay_provider"


def _resolve_ep(extension_point: ExtensionPoint | str) -> ExtensionPoint:
    if isinstance(extension_point, ExtensionPoint):
        return extension_point
    val = str(getattr(extension_point, "value", extension_point)).strip().lower()
    return ExtensionPoint(val)


class ExtensionRegistry:
    """Registry engine tracking extensions across all 8 extension points."""

    def __init__(self) -> None:
        self._registry: Dict[ExtensionPoint, Dict[str, Any]] = {
            ep: {} for ep in ExtensionPoint
        }

    def register_extension(self, extension_point: ExtensionPoint | str, name: str, extension_obj: Any) -> None:
        """Register an extension object under a specific extension point."""
        ep = _resolve_ep(extension_point)
        key = name.strip().lower()

        if key in self._registry[ep]:
            raise DuplicatePluginError(f"Extension '{name}' already registered under extension point '{ep.value}'")

        self._registry[ep][key] = extension_obj

    def get_extensions(self, extension_point: ExtensionPoint | str) -> List[Any]:
        """Return list of all registered objects for an extension point."""
        ep = _resolve_ep(extension_point)
        return list(self._registry[ep].values())

    def get_extension(self, extension_point: ExtensionPoint | str, name: str) -> Optional[Any]:
        """Fetch specific registered extension object by name."""
        ep = _resolve_ep(extension_point)
        key = name.strip().lower()
        return self._registry[ep].get(key)

    def list_all_extensions(self) -> Dict[str, List[str]]:
        """Return summary mapping of extension points to registered extension names."""
        return {
            ep.value: list(self._registry[ep].keys())
            for ep in ExtensionPoint
        }


# Global default extension registry instance
default_extension_registry = ExtensionRegistry()


def get_default_extension_registry() -> ExtensionRegistry:
    """Returns global default extension registry instance."""
    return default_extension_registry
