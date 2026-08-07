"""
Unit tests for Plugin SDK Contracts and Manifest (PR-P1).
"""

import pytest

from ape.plugins.contracts import ApePlugin
from ape.plugins.exceptions import PluginIncompatibleError, PluginLoadError
from ape.plugins.manifest import PluginManifest


class MockValidPlugin:
    name = "ape-node"
    version = "1.0.0"
    api_version = "1"

    def register(self, registry):
        registry.register_extension("runtime_pack", self.name, self)


def test_plugin_protocol_compliance():
    plugin = MockValidPlugin()
    assert isinstance(plugin, ApePlugin)
    assert plugin.name == "ape-node"
    assert plugin.version == "1.0.0"
    assert plugin.api_version == "1"


def test_plugin_manifest_parsing():
    data = {
        "name": "ape-go",
        "version": "2.1.0",
        "api_version": "1",
        "entrypoint": "ape_go.plugin:Plugin",
        "requires": ["runtime", "quality"],
    }
    manifest = PluginManifest.from_dict(data)
    assert manifest.name == "ape-go"
    assert manifest.version == "2.1.0"
    assert manifest.requires == ["runtime", "quality"]
    assert manifest.to_dict()["api_version"] == "1"
