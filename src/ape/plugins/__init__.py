"""
APE Plugin SDK & Extension Subsystem — RFC-022 / PR-P1 to PR-P4 Specification.
"""

from ape.plugins.contracts import ApePlugin
from ape.plugins.exceptions import (
    DuplicatePluginError,
    PluginError,
    PluginIncompatibleError,
    PluginLoadError,
)
from ape.plugins.loader import PluginLoader
from ape.plugins.manifest import PluginManifest
from ape.plugins.registry import (
    ExtensionPoint,
    ExtensionRegistry,
    get_default_extension_registry,
)

__all__ = [
    "ApePlugin",
    "PluginManifest",
    "PluginError",
    "PluginLoadError",
    "PluginIncompatibleError",
    "DuplicatePluginError",
    "ExtensionPoint",
    "ExtensionRegistry",
    "get_default_extension_registry",
    "PluginLoader",
]
