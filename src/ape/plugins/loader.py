"""
Automatic Plugin Discovery, Loader & Versioning Engine — RFC-022 / PR-P3 & PR-P4 Specification.
Supports python entry_points group 'ape.plugins' and directory scanning under .ape/plugins/.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from ape.plugins.contracts import ApePlugin
from ape.plugins.exceptions import PluginIncompatibleError, PluginLoadError
from ape.plugins.manifest import PluginManifest
from ape.plugins.registry import ExtensionRegistry, get_default_extension_registry

HOST_API_VERSION = "1"


class PluginLoader:
    """Discovers, loads, validates, and registers plugins into ExtensionRegistry."""

    def __init__(
        self,
        project_root: Path,
        registry: Optional[ExtensionRegistry] = None,
        strict_versioning: bool = False,
    ) -> None:
        self.project_root = Path(project_root)
        self.registry = registry or get_default_extension_registry()
        self.strict_versioning = strict_versioning
        self.loaded_plugins: Dict[str, ApePlugin] = {}

    def discover_entry_points(self) -> List[Any]:
        """Discover third-party plugins registered under python entry_points group 'ape.plugins'."""
        plugins: List[Any] = []
        try:
            if sys.version_info >= (3, 10):
                eps = importlib.metadata.entry_points(group="ape.plugins")
            else:
                eps = importlib.metadata.entry_points().get("ape.plugins", [])

            for ep in eps:
                try:
                    plugin_cls = ep.load()
                    plugins.append(plugin_cls)
                except Exception as exc:
                    if self.strict_versioning:
                        raise PluginLoadError(f"Failed to load entrypoint plugin '{ep.name}': {exc}")
        except Exception:
            pass
        return plugins

    def discover_directory(self, plugins_dir: Optional[Path] = None) -> List[Path]:
        """Discover plugin directories containing manifest.json or plugin.py under .ape/plugins/."""
        target_dir = plugins_dir or (self.project_root / ".ape" / "plugins")
        discovered: List[Path] = []

        if target_dir.exists() and target_dir.is_dir():
            for child in target_dir.iterdir():
                if child.is_dir() and ((child / "manifest.json").exists() or (child / "plugin.py").exists()):
                    discovered.append(child)

        return discovered

    def validate_compatibility(self, api_version: str, plugin_name: str) -> None:
        """Validate plugin api_version compatibility against HOST_API_VERSION."""
        if str(api_version).strip() != HOST_API_VERSION:
            msg = (
                f"Plugin '{plugin_name}' requires api_version '{api_version}', "
                f"but host engine supports api_version '{HOST_API_VERSION}'"
            )
            if self.strict_versioning:
                raise PluginIncompatibleError(msg)

    def load_plugin_instance(self, plugin_obj: Any) -> ApePlugin:
        """Instantiate and validate plugin object against ApePlugin contract."""
        instance = plugin_obj() if isinstance(plugin_obj, type) else plugin_obj

        name = getattr(instance, "name", None)
        version = getattr(instance, "version", None)
        api_version = getattr(instance, "api_version", "1")

        if not name or not version:
            raise PluginLoadError(f"Object {instance} missing required 'name' or 'version' attribute")

        self.validate_compatibility(str(api_version), str(name))
        return instance

    def register_plugin(self, plugin: ApePlugin) -> None:
        """Register plugin into ExtensionRegistry and track in loaded_plugins."""
        name = str(plugin.name).lower()
        if name in self.loaded_plugins:
            return

        plugin.register(self.registry)
        self.loaded_plugins[name] = plugin

    def load_and_register_all(self) -> Dict[str, ApePlugin]:
        """Discover, load, and register all entrypoint and directory plugins."""
        # 1. Discover entrypoints
        for ep_obj in self.discover_entry_points():
            try:
                plugin = self.load_plugin_instance(ep_obj)
                self.register_plugin(plugin)
            except Exception as exc:
                if self.strict_versioning:
                    raise

        # 2. Discover local directory plugins
        for p_dir in self.discover_directory():
            manifest_file = p_dir / "manifest.json"
            if manifest_file.exists():
                try:
                    data = json.loads(manifest_file.read_text(encoding="utf-8"))
                    manifest = PluginManifest.from_dict(data)
                    self.validate_compatibility(manifest.api_version, manifest.name)
                except Exception as exc:
                    if self.strict_versioning:
                        raise PluginLoadError(f"Invalid plugin manifest in '{p_dir}': {exc}")

        return self.loaded_plugins
