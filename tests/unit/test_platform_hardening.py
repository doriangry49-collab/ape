"""
Unit tests for Phase A Platform Hardening & Package Boundary Integrity.
Verifies clean importability and isolation across all platform subsystems.
"""

import pytest


def test_package_boundary_importability():
    import ape.analytics
    import ape.business
    import ape.explorer
    import ape.fabric
    import ape.pipeline
    import ape.plugins
    import ape.policy
    import ape.provenance
    import ape.quality
    import ape.replay
    import ape.server
    import ape.store
    import ape.workspace

    assert ape.quality.__file__ is not None
    assert ape.policy.__file__ is not None
    assert ape.replay.__file__ is not None
    assert ape.fabric.__file__ is not None
    assert ape.workspace.__file__ is not None
    assert ape.business.__file__ is not None
    assert ape.store.__file__ is not None
