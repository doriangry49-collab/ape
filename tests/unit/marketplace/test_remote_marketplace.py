"""
Unit tests for RemoteMarketplaceRegistry (EPIC G6-4).
"""

import pytest

from ape.marketplace.contracts import MarketplacePackage
from ape.marketplace.remote import RemoteMarketplaceRegistry


def test_remote_marketplace_registry():
    reg = RemoteMarketplaceRegistry()
    pkg = MarketplacePackage(
        package_id="ape-plugin-rust",
        name="Rust Language Pack",
        version="1.0.0",
        package_type="plugin",
        description="Official Rust compiler pack",
        author="APE Official",
        signature_sha256="mock_sha256",
        verified=True,
    )

    assert reg.publish_package(pkg) is True
    res = reg.query_remote("rust")
    assert len(res) == 1
    assert res[0].package_id == "ape-plugin-rust"
