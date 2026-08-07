"""
Unit tests for Agent Factory Engine (EPIC-11E).
"""

from pathlib import Path
import pytest

from ape.factory import AgentFactoryEngine, GeneratedFabricAgent
from ape.marketplace import MarketplaceIndex


def test_agent_factory_generation_and_publishing(tmp_path: Path):
    index = MarketplaceIndex(storage_dir=tmp_path / ".marketplace")
    factory = AgentFactoryEngine(tmp_path, marketplace_index=index)

    meta = factory.generate_agent(
        role="security",
        capabilities=["bandit_scan", "secret_check"],
        description="Automated Security Auditor Agent",
    )

    assert meta.agent_name == "factory_security_agent"
    assert meta.role == "security"
    assert meta.quality_audit_passed is True
    assert meta.confidence_score > 80.0

    # Verify published package in MarketplaceIndex
    pkg = index.get_package(meta.package_id)
    assert pkg is not None
    assert pkg.package_type == "agent"
    assert pkg.verified is True
