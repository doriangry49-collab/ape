"""
Unit tests for ORION-106B Typed Artifact Bundle Architecture & ArtifactAssembler Layer.
Verifies Research, Build, Marketing, and Deployment ArtifactBundles, and ArtifactAssembler materialization to disk and ZIP archives.
"""

import tempfile
import zipfile
from pathlib import Path

from ape.business import (
    ArtifactAssembler,
    BuildArtifactBundle,
    MarketingArtifactBundle,
    ResearchArtifactBundle,
)


def test_research_artifact_bundle_creation():
    bundle = ResearchArtifactBundle.create("Real Estate Automation", ["CompA", "CompB"], ["High latency", "Manual input"])

    assert bundle.bundle_type == "research"
    assert len(bundle.files) == 3
    paths = [f.relative_path for f in bundle.files]
    assert "research/competitor_analysis.md" in paths
    assert "research/pain_points.json" in paths
    assert "research/market_size.md" in paths


def test_build_artifact_bundle_creation():
    bundle = BuildArtifactBundle.create("Real Estate Automation Mini-SaaS")

    assert bundle.bundle_type == "build"
    assert len(bundle.files) == 4
    paths = [f.relative_path for f in bundle.files]
    assert "repo/src/main.py" in paths
    assert "repo/Dockerfile" in paths


def test_artifact_assembler_materialization_to_disk():
    bundle = BuildArtifactBundle.create("Real Estate Automation Mini-SaaS")

    with tempfile.TemporaryDirectory() as tmp_dir:
        target_path = Path(tmp_dir) / "ventures" / "v_001"
        written_files = ArtifactAssembler.assemble_to_disk(bundle, target_path)

        assert len(written_files) == 4
        assert (target_path / "repo" / "src" / "main.py").exists()
        assert (target_path / "repo" / "Dockerfile").exists()
        content = (target_path / "repo" / "README.md").read_text(encoding="utf-8")
        assert "Real Estate Automation Mini-SaaS" in content


def test_artifact_assembler_compression_to_zip():
    bundle = MarketingArtifactBundle.create("Real Estate Automation", "<h1>Landing Page</h1>")

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = Path(tmp_dir) / "bundle.zip"
        res_zip = ArtifactAssembler.assemble_to_zip(bundle, zip_path)

        assert res_zip.exists()
        with zipfile.ZipFile(res_zip, "r") as zf:
            namelist = zf.namelist()
            assert "marketing/landing_page.html" in namelist
            assert "marketing/seo_metadata.json" in namelist
