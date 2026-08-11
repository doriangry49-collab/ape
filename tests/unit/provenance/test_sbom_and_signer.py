"""
Unit tests for SBOM Generator and Artifact Signer (PR-L1).
"""

from pathlib import Path

from ape.provenance.sbom import SBOMGenerator
from ape.provenance.signer import ArtifactSigner


def test_sbom_spdx_generation(tmp_path: Path):
    generator = SBOMGenerator(tmp_path)
    spdx = generator.generate_spdx("calc_app", ["main.py"])

    assert spdx["spdxVersion"] == "SPDX-2.3"
    assert len(spdx["packages"]) >= 2


def test_artifact_signer_merkle_root(tmp_path: Path):
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")

    signer = ArtifactSigner(tmp_path)
    signed = signer.sign_deliverables("calc_app", ["main.py"])

    assert "merkle_root" in signed
    assert len(signed["merkle_root"]) == 64
    assert signed["signature_algorithm"] == "SHA-256"
