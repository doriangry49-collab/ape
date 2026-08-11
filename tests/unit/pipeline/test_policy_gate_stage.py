"""Unit tests for PolicyGateStage."""

import json
from pathlib import Path

from ape.pipeline.contracts import ExecutionContext, StageStatus
from ape.pipeline.stages.policy_gate import PolicyGateStage


def test_policy_gate_stage_build_success(tmp_path: Path):
    decisions_dir = tmp_path / ".build" / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    decision_data = {
        "decision_id": "dec_build_001",
        "decision": "BUILD",
        "evidence_hash": "sha256_build_hash",
        "score": 85,
        "reason": "Strong market demand",
        "approval_required": False,
    }
    (decisions_dir / "test-build-topic.json").write_text(
        json.dumps(decision_data), encoding="utf-8"
    )

    stage = PolicyGateStage(project_root=tmp_path)
    ctx = ExecutionContext(run_id="run-policy-1", topic_slug="test-build-topic")

    res = stage.execute(ctx, [])
    assert res.status == StageStatus.SUCCESS
    assert res.output_data["policy_decision"] == "BUILD"
    assert res.output_data["decision_id"] == "dec_build_001"
    assert res.output_data["decision_score"] == 85
    assert res.output_data["decision_reason"] == "Strong market demand"


def test_policy_gate_stage_fast_fail_blocked(tmp_path: Path):
    decisions_dir = tmp_path / ".build" / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    decision_data = {
        "decision_id": "dec_watch_002",
        "decision": "WATCH",
        "score": 40,
        "reason": "Insufficient evidence",
    }
    (decisions_dir / "test-watch-topic.json").write_text(
        json.dumps(decision_data), encoding="utf-8"
    )

    stage = PolicyGateStage(project_root=tmp_path)
    ctx = ExecutionContext(run_id="run-policy-2", topic_slug="test-watch-topic")

    res = stage.execute(ctx, [])
    assert res.status == StageStatus.BLOCKED
    assert res.output_data["policy_decision"] == "WATCH"
    assert res.evidence["failure_reason"] == "POLICY_DECISION_WATCH"
    assert "Execution blocked" in (res.error or "")


def test_policy_gate_stage_missing_artifact(tmp_path: Path):
    stage = PolicyGateStage(project_root=tmp_path)
    ctx = ExecutionContext(run_id="run-policy-3", topic_slug="unknown-topic")

    res = stage.execute(ctx, [])
    assert res.status == StageStatus.FAILED
    assert res.evidence["failure_reason"] == "DECISION_ARTIFACT_MISSING"
    assert "No decision artifact found" in (res.error or "")
