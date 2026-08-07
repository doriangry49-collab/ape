"""
Unit tests for Quality OS PR-Q3 Hardening, Artifact Collector, and Evidence Binder.
"""

import json
from pathlib import Path
import sys
import pytest

from ape.quality.contracts import (
    QualityReport,
    ValidationContext,
    ValidationResult,
    ValidationStatus,
)
from ape.quality.evidence import QualityEvidenceBinder
from ape.quality.reporter import QualityReportCollector
from ape.quality.runner import QualityRunner, SubprocessRunner
from ape.quality.validators.pytest_validator import PytestValidator


def test_quality_report_collector_saves_reports_and_manifests(tmp_path: Path):
    """QualityReportCollector must write quality_report.json, metrics.json, validator_manifest.json, junit.xml, coverage.json."""
    collector = QualityReportCollector(tmp_path)
    res = ValidationResult(
        validator_name="pytest",
        status=ValidationStatus.PASS,
        score=100.0,
        duration_ms=45.0,
        metrics={"total_tests": 5, "failures": 0},
    )
    report = QualityReport(
        overall_score=100.0,
        quality_audit_passed=True,
        results=[res],
        summary={"total_validators": 1, "passed": 1},
    )

    saved_paths = collector.save_report(report, topic_slug="test_topic", validator_names=["pytest"])

    assert "quality_report.json" in saved_paths
    assert "metrics.json" in saved_paths
    assert "validator_manifest.json" in saved_paths
    assert "junit.xml" in saved_paths
    assert "coverage.json" in saved_paths

    # Verify quality_report.json content
    q_data = json.loads(saved_paths["quality_report.json"].read_text(encoding="utf-8"))
    assert q_data["overall_score"] == 100.0
    assert q_data["topic_slug"] == "test_topic"

    # Verify metrics.json
    m_data = json.loads(saved_paths["metrics.json"].read_text(encoding="utf-8"))
    assert m_data["passed_validators"] == 1
    assert m_data["validator_metrics"]["pytest"]["total_tests"] == 5


def test_quality_evidence_binder_merkle_root(tmp_path: Path):
    """QualityEvidenceBinder must compute SHA-256 hashes and deterministic quality_merkle_root digest."""
    collector = QualityReportCollector(tmp_path)
    report = QualityReport(overall_score=100.0, quality_audit_passed=True)
    collector.save_report(report)

    # Create dummy log file
    log_dir = tmp_path / ".build" / "quality" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "pytest.log").write_text("pytest log content", encoding="utf-8")

    binder = QualityEvidenceBinder(tmp_path)
    manifest = binder.build_evidence_manifest()

    assert manifest["artifact_count"] >= 5
    assert "reports/quality_report.json" in manifest["artifact_hashes"]
    assert "logs/pytest.log" in manifest["artifact_hashes"]
    assert len(manifest["quality_merkle_root"]) == 64  # SHA-256 hex digest


def test_subprocess_runner_retry_mechanism(tmp_path: Path):
    """SubprocessRunner must attempt retries when command fails and retries are enabled."""
    runner = SubprocessRunner()

    # Run command that fails (exit 1)
    cmd = [sys.executable, "-c", "import sys; sys.exit(1)"]
    sub_res = runner.run(cmd, cwd=tmp_path, max_retries=2, retry_delay_sec=0.01)

    assert sub_res.returncode == 1
    assert sub_res.timed_out is False


def test_pytest_validator_junit_xml_parsing(tmp_path: Path):
    """PytestValidator must write --junitxml and parse JUnit XML metrics."""
    test_file = tmp_path / "test_sample.py"
    test_file.write_text("def test_ok(): assert True\n", encoding="utf-8")

    validator = PytestValidator()
    context = ValidationContext(project_root=tmp_path, topic_slug="sample", deliverables=["test_sample.py"])

    res = validator.validate(context)

    assert res.status == ValidationStatus.PASS
    assert res.metrics.get("total_tests") == 1
    assert res.metrics.get("failures") == 0
    assert (tmp_path / ".build" / "quality" / "reports" / "junit.xml").exists()
