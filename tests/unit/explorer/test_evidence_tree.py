"""
Unit tests for Evidence Explorer (PR-K1).
"""

from pathlib import Path

from ape.explorer.tree import EvidenceTreeExplorer


def test_evidence_tree_explorer_rendering(tmp_path: Path):
    explorer = EvidenceTreeExplorer(tmp_path)
    cli_text = explorer.render_cli("build-2026-001")

    assert "Evidence Explorer" in cli_text
    assert "EVIDENCE TREE HIERARCHY" in cli_text
    assert "Research Signals" in cli_text
    assert "Supply Chain Provenance" in cli_text
