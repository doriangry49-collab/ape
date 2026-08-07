"""
Unit tests for Plugin Loader and Versioning Guard (PR-P3 / PR-P4).
"""

import json
from pathlib import Path
import pytest

from ape.plugins.exceptions import PluginIncompatibleError, PluginLoadError
from ape.plugins.loader import PluginLoader
from ape.plugins.registry import ExtensionRegistry


class DummyValidPlugin:
    name = "ape-k8s"
    version = "1.0.0"
    api_version = "1"

    def register(self, registry):
        registry.register_extension("validator", self.name, self)


class DummyIncompatiblePlugin:
    name = "ape-future"
    version = "99.0.0"
    api_version = "99"

    def register(self, registry):
        pass


def test_plugin_loader_registration_flow(tmp_path: Path):
    registry = ExtensionRegistry()
    loader = PluginLoader(tmp_path, registry=registry)

    inst = loader.load_plugin_instance(DummyValidPlugin)
    loader.register_plugin(inst)

    assert "ape-k8s" in loader.loaded_plugins
    assert registry.get_extension("validator", "ape-k8s") is not None


def test_plugin_loader_version_incompatibility(tmp_path: Path):
    registry = ExtensionRegistry()
    loader = PluginLoader(tmp_path, registry=registry, strict_versioning=True)

    with pytest.raises(PluginIncompatibleError, match="requires api_version '99'"):
        loader.load_plugin_instance(DummyIncompatiblePlugin)


def test_plugin_loader_directory_discovery(tmp_path: Path):
    plugins_dir = tmp_path / ".ape" / "plugins" / "my_plugin"
    plugins_dir.mkdir(parents=True, exist_ok=True)

    manifest_file = plugins_dir / "manifest.json"
    manifest_file.write_text(json.dumps({
        "name": "my_plugin",
        "version": "1.0.0",
        "api_version": "1",
    }), encoding="utf-8")

    loader = PluginLoader(tmp_path)
    discovered = loader.discover_directory()
    assert len(discovered) == 1
    assert discovered[0].name == "my_plugin"
