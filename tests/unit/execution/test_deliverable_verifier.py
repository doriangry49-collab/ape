"""
Unit tests for DeliverableVerifier hardening.

Covers:
1. Zero-byte file -> FAIL
2. Valid JSON file -> PASS
3. Invalid JSON file (.json extension, bad syntax) -> FAIL
4. Non-JSON file with content -> PASS (no JSON check)
5. Existing behavior still works (file exists -> PASS for non-empty, non-JSON files)
6. Backward compatibility: result unpacks as (ok, missing) and has .passed
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from ape.intelligence.execution.verifier import DeliverableVerifier


@pytest.fixture
def tmp_root(tmp_path: Path) -> Path:
    return tmp_path


class TestDeliverableVerifierHardening:
    """Tests for the hardened DeliverableVerifier."""

    def test_zero_byte_file_fails(self, tmp_root: Path) -> None:
        """A zero-byte file should be treated as invalid/missing."""
        target = tmp_root / "empty.txt"
        target.write_text("")

        verifier = DeliverableVerifier(project_root=tmp_root)
        result = verifier.verify(["empty.txt"])

        assert result.passed is False
        assert "empty.txt" in result.missing_items

    def test_valid_json_file_passes(self, tmp_root: Path) -> None:
        """A valid JSON file should pass verification."""
        target = tmp_root / "config.json"
        target.write_text(json.dumps({"key": "value", "count": 42}))

        verifier = DeliverableVerifier(project_root=tmp_root)
        result = verifier.verify(["config.json"])

        assert result.passed is True
        assert result.missing_items == []

    def test_invalid_json_file_fails(self, tmp_root: Path) -> None:
        """A .json file with bad syntax should be treated as invalid/missing."""
        target = tmp_root / "broken.json"
        target.write_text("{invalid json content, missing quotes}")

        verifier = DeliverableVerifier(project_root=tmp_root)
        result = verifier.verify(["broken.json"])

        assert result.passed is False
        assert "broken.json" in result.missing_items

    def test_non_json_file_with_content_passes(self, tmp_root: Path) -> None:
        """A non-JSON file with content should pass without JSON validation."""
        target = tmp_root / "readme.md"
        target.write_text("# Hello World\n\nThis is a readme file.")

        verifier = DeliverableVerifier(project_root=tmp_root)
        result = verifier.verify(["readme.md"])

        assert result.passed is True
        assert result.missing_items == []

    def test_existing_behavior_non_empty_non_json_passes(self, tmp_root: Path) -> None:
        """Existing behavior: a non-empty, non-JSON file that exists should pass."""
        target = tmp_root / "output.csv"
        target.write_text("col1,col2\n1,2\n3,4\n")

        verifier = DeliverableVerifier(project_root=tmp_root)
        result = verifier.verify(["output.csv"])

        assert result.passed is True
        assert result.missing_items == []

    def test_backward_compatibility_unpacking(self, tmp_root: Path) -> None:
        """Result should unpack as (ok, missing) for backward compatibility."""
        target = tmp_root / "data.json"
        target.write_text(json.dumps({"valid": True}))

        verifier = DeliverableVerifier(project_root=tmp_root)
        ok, missing = verifier.verify(["data.json"])

        assert ok is True
        assert missing == []

    def test_backward_compatibility_missing_unpacking(self, tmp_root: Path) -> None:
        """Result should unpack correctly when deliverables are missing."""
        verifier = DeliverableVerifier(project_root=tmp_root)
        ok, missing = verifier.verify(["nonexistent.txt"])

        assert ok is False
        assert "nonexistent.txt" in missing

    def test_single_string_deliverable(self, tmp_root: Path) -> None:
        """A single string deliverable should be treated as [deliverables]."""
        target = tmp_root / "single.txt"
        target.write_text("content")

        verifier = DeliverableVerifier(project_root=tmp_root)
        result = verifier.verify("single.txt")

        assert result.passed is True
        assert result.missing_items == []

    def test_default_project_root(self) -> None:
        """DeliverableVerifier() should default project_root to Path('.')."""
        verifier = DeliverableVerifier()
        assert verifier._root == Path(".")

    def test_default_dry_run(self) -> None:
        """DeliverableVerifier() should default dry_run to False."""
        verifier = DeliverableVerifier()
        assert verifier._dry_run is False

    def test_dry_run_skips_verification(self, tmp_root: Path) -> None:
        """In dry-run mode, verification is skipped (returns True, [])."""
        verifier = DeliverableVerifier(project_root=tmp_root, dry_run=True)
        result = verifier.verify(["nonexistent.txt"])

        assert result.passed is True
        assert result.missing_items == []

    def test_empty_deliverables_list(self, tmp_root: Path) -> None:
        """An empty deliverables list should return (True, [])."""
        verifier = DeliverableVerifier(project_root=tmp_root)
        result = verifier.verify([])

        assert result.passed is True
        assert result.missing_items == []

    def test_json_case_insensitive_extension(self, tmp_root: Path) -> None:
        """JSON validation should be case-insensitive for the .json extension."""
        target = tmp_root / "data.JSON"
        target.write_text("{bad json")

        verifier = DeliverableVerifier(project_root=tmp_root)
        result = verifier.verify(["data.JSON"])

        assert result.passed is False
        assert "data.JSON" in result.missing_items

    def test_multiple_deliverables_all_pass(self, tmp_root: Path) -> None:
        """All deliverables pass when all files are valid."""
        (tmp_root / "a.txt").write_text("hello")
        (tmp_root / "b.json").write_text(json.dumps({"x": 1}))

        verifier = DeliverableVerifier(project_root=tmp_root)
        result = verifier.verify(["a.txt", "b.json"])

        assert result.passed is True
        assert result.missing_items == []

    def test_multiple_deliverables_one_fails(self, tmp_root: Path) -> None:
        """Verification fails if any deliverable is invalid."""
        (tmp_root / "good.txt").write_text("hello")
        (tmp_root / "bad.json").write_text("not json")

        verifier = DeliverableVerifier(project_root=tmp_root)
        result = verifier.verify(["good.txt", "bad.json"])

        assert result.passed is False
        assert "bad.json" in result.missing_items
