"""
Plugin SDK Custom Exceptions — RFC-022 / PR-P1 Specification.
Defines exceptions for plugin loading, version incompatibility, and registration collisions.
"""


class PluginError(Exception):
    """Base exception for all APE Plugin SDK errors."""
    pass


class PluginLoadError(PluginError):
    """Raised when a plugin fails to import, instantiate, or register."""
    pass


class PluginIncompatibleError(PluginError):
    """Raised when a plugin's api_version does not match host APE engine version."""
    pass


class DuplicatePluginError(PluginError):
    """Raised when attempting to register a plugin with a duplicate name and extension point."""
    pass
