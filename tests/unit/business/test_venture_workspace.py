"""
Unit tests for ORION-107 Venture WorkspaceManager & Multi-Venture Isolation.
Verifies multi-venture directory isolation, bundle materialization into venture subfolders,
and release archive packaging.
"""

import tempfile
import zipfile
from pathlib import Path

from ape.business import (
    BuildArtifactBundle,
    MarketingArtifactBundle,
    ResearchArtifactBundle,
    VentureWorkspaceManager,
)


def test_venture_workspace_creation_and_isolation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        manager = VentureWorkspaceManager(root_dir=Path(tmp_dir) / "ventures")
        w1 = manager.create_workspace("v_real_estate_001")
        w2 = manager.create_workspace("v_youtube_studio_002")

        assert w1.exists()
        assert w2.exists()
        assert w1 != w2
        assert set(manager.list_ventures()) == {"v_real_estate_001", "v_youtube_studio_002"}


def test_save_bundle_into_isolated_venture_workspace():
    with tempfile.TemporaryDirectory() as tmp_dir:
        manager = VentureWorkspaceManager(root_dir=Path(tmp_dir) / "ventures")
        venture_id = "v_real_estate_001"

        res_bundle = ResearchArtifactBundle.create("Real Estate", ["CompA"], ["PainA"])
        build_bundle = BuildArtifactBundle.create("Real Estate Automation Mini-SaaS")

        written_res = manager.save_bundle(venture_id, res_bundle)
        written_build = manager.save_bundle(venture_id, build_bundle)

        workspace_path = manager.get_workspace_path(venture_id)

        assert (workspace_path / "research" / "competitor_analysis.md").exists()
        assert (workspace_path / "repo" / "src" / "main.py").exists()
        assert (workspace_path / "repo" / "Dockerfile").exists()


def test_package_venture_release_archive():
    with tempfile.TemporaryDirectory() as tmp_dir:
        manager = VentureWorkspaceManager(root_dir=Path(tmp_dir) / "ventures")
        venture_id = "v_real_estate_001"

        res_bundle = ResearchArtifactBundle.create("Real Estate", ["CompA"], ["PainA"])
        build_bundle = BuildArtifactBundle.create("Real Estate Automation Mini-SaaS")
        mkt_bundle = MarketingArtifactBundle.create("Real Estate Automation", "<h1>Landing Page</h1>")

        manager.save_bundle(venture_id, res_bundle)
        manager.save_bundle(venture_id, build_bundle)
        manager.save_bundle(venture_id, mkt_bundle)

        release_zip = manager.package_venture_release(venture_id)

        assert release_zip.exists()
        with zipfile.ZipFile(release_zip, "r") as zf:
            namelist = zf.namelist()
            assert "research/competitor_analysis.md" in namelist
            assert "repo/src/main.py" in namelist
            assert "marketing/landing_page.html" in namelist
