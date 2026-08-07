"""
Unit tests for Replay & Reproducibility Engine (PR-G1 / PR-G2).
"""

import json
from pathlib import Path
import pytest

from ape.replay.engine import ReplayEngine, ReplayPlanner, ReplayReporter, ReplayVerifier
from ape.replay.models import ReplayReport


def test_replay_planner_snapshot_loading(tmp_path: Path):
    reports_dir = tmp_path / ".build" / "quality" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    quality_file = reports_dir / "quality_report.json"
    quality_file.write_text(json.dumps({
        "release_confidence": 95.0,
        "quality_profile": "standard",
        "overall_score": 95.0,
    }), encoding="utf-8")

    planner = ReplayPlanner(tmp_path)
    snapshot = planner.load_build_snapshot("test_app")

    assert snapshot["topic_slug"] == "test_app"
    assert snapshot["quality_report"]["release_confidence"] == 95.0


def test_replay_verifier_reproducible_match():
    snapshot = {
        "build_id": "build-001",
        "topic_slug": "test_app",
        "quality_report": {
            "release_confidence": 92.0,
            "quality_profile": "standard",
            "evidence_manifest": {"merkle_root": "abc123hash"},
        },
    }

    class MockReplayQR:
        release_confidence = 92.0
        overall_score = 92.0
        quality_audit_passed = True
        evidence_manifest = {"merkle_root": "abc123hash"}
        results = []

    report = ReplayVerifier.verify(snapshot, MockReplayQR())
    assert report.is_reproducible is True
    assert report.confidence_delta == 0.0
    assert report.merkle_root_match is True


def test_replay_reporter_cli_rendering():
    report = ReplayReport(
        build_id="build-2026-001",
        topic_slug="ledger_api",
        quality_profile="standard",
        is_reproducible=True,
        confidence_delta=0.0,
        original_confidence=92.0,
        replay_confidence=92.0,
        merkle_root_match=True,
        artifact_hash_match=True,
        runtime_passed=True,
    )

    rendered = ReplayReporter.render_cli(report)
    assert "ledger_api" in rendered
    assert "STANDARD" in rendered
    assert "REPRODUCIBLE" in rendered
    assert "0.00" in rendered


def test_replay_engine_end_to_end(tmp_path: Path):
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")

    reports_dir = tmp_path / ".build" / "quality" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "quality_report.json").write_text(json.dumps({
        "release_confidence": 100.0,
        "quality_profile": "fast",
    }), encoding="utf-8")

    engine = ReplayEngine(tmp_path)
    report = engine.replay("test_app", quality_profile="fast")

    assert isinstance(report, ReplayReport)
    assert report.is_reproducible is True
