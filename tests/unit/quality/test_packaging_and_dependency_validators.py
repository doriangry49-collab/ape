"""
Unit tests for Capability Milestone C: Packaging, Dependency, and Release Confidence Engine.
"""

from pathlib import Path

from ape.quality.contracts import (
    ValidationContext,
    ValidationStatus,
)
from ape.quality.runner import QualityRunner
from ape.quality.validators.dependency_validator import DependencyValidator
from ape.quality.validators.packaging_validator import PackagingValidator


def test_dependency_validator_pass_and_warn(tmp_path: Path):
    """DependencyValidator must pass when dependencies match imports and warn on undeclared imports."""
    (tmp_path / "requirements.txt").write_text("pytest==8.0.0\nrequests>=2.0.0\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("import os\nimport requests\n", encoding="utf-8")

    validator = DependencyValidator()
    context = ValidationContext(project_root=tmp_path, topic_slug="dep_test", deliverables=["app.py"])

    res = validator.validate(context)
    assert res.status == ValidationStatus.PASS
    assert res.metrics["declared_count"] == 2
    assert res.metrics["undeclared_count"] == 0

    # Add undeclared import
    (tmp_path / "app.py").write_text("import os\nimport requests\nimport numpy\n", encoding="utf-8")
    res_warn = validator.validate(context)
    assert res_warn.status == ValidationStatus.WARN
    assert res_warn.metrics["undeclared_count"] == 1


def test_packaging_validator_structure_and_containment(tmp_path: Path):
    """PackagingValidator must pass with pyproject.toml and entrypoint, and fail on containment breach."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test-app'\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")

    validator = PackagingValidator()
    context = ValidationContext(project_root=tmp_path, topic_slug="pack_test", deliverables=["main.py"])

    res = validator.validate(context)
    assert res.status == ValidationStatus.PASS
    assert res.metrics["has_pyproject"] is True
    assert res.metrics["has_entrypoint"] is True

    # Test containment breach
    context_breach = ValidationContext(project_root=tmp_path, topic_slug="breach", deliverables=["../outside.py"])
    res_fail = validator.validate(context_breach)
    assert res_fail.status == ValidationStatus.FAIL
    assert res_fail.metrics["escaped_count"] == 1


def test_quality_runner_release_confidence_and_risk_level(tmp_path: Path):
    """QualityRunner must calculate release_confidence, risk_level, and capability_coverage."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "test_main.py").write_text("def test_dummy(): assert True\n", encoding="utf-8")

    runner = QualityRunner()
    context = ValidationContext(project_root=tmp_path, topic_slug="full_test", deliverables=["main.py", "test_main.py"])

    report = runner.run(context)

    assert report.quality_audit_passed is True
    assert report.release_confidence >= 85.0
    assert report.risk_level == "LOW"
    assert "correctness" in report.capability_coverage
    assert "executability" in report.capability_coverage
    assert "packaging" in report.capability_coverage
