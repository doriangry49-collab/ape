"""
Unit tests for Extension Points Registry (PR-P2).
"""

import pytest

from ape.plugins.exceptions import DuplicatePluginError
from ape.plugins.registry import ExtensionPoint, ExtensionRegistry


def test_extension_registry_registration():
    registry = ExtensionRegistry()

    dummy_validator = {"name": "custom_sec"}
    registry.register_extension(ExtensionPoint.VALIDATOR, "custom_sec", dummy_validator)

    dummy_pack = {"name": "go_pack"}
    registry.register_extension("runtime_pack", "go_pack", dummy_pack)

    validators = registry.get_extensions(ExtensionPoint.VALIDATOR)
    assert dummy_validator in validators

    packs = registry.get_extensions("runtime_pack")
    assert dummy_pack in packs


def test_extension_registry_duplicate_rejection():
    registry = ExtensionRegistry()
    registry.register_extension("validator", "duplicate_name", {})

    with pytest.raises(DuplicatePluginError, match="already registered"):
        registry.register_extension("validator", "duplicate_name", {})


def test_extension_registry_all_list():
    registry = ExtensionRegistry()
    registry.register_extension("validator", "val_1", {})
    registry.register_extension("dashboard_widget", "widget_1", {})

    all_summary = registry.list_all_extensions()
    assert "val_1" in all_summary["validator"]
    assert "widget_1" in all_summary["dashboard_widget"]
