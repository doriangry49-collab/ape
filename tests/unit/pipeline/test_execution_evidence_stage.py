"""Unit tests for ExecutionEvidenceStage."""

from pathlib import Path
import pytest

from ape.pipeline.contracts import ExecutionContext, StageResult, StageStatus
from ape.pipeline.stages.execution_evidence import ExecutionEvidenceStage


def test_execution_evidence_stage_pure_bundle_aggregation(tmp_path: Path):
    stage = ExecutionEvidenceStage()
    ctx = ExecutionContext(run_id="run-ev-1", topic_slug="test-topic")

    plan_res = StageResult(
        stage_name="execution_plan",
        status=StageStatus.SUCCESS,
        output_data={"execution_plan": {"task_count": 2}},
        evidence={"stage_hash": "hash_plan_123"},
    )
    policy_res = StageResult(
        stage_name="policy_gate",
        status=StageStatus.SUCCESS,
        output_data={
            "policy_decision": "BUILD",
            "decision_id": "dec_999",
            "decision_score": 90,
        },
        evidence={"stage_hash": "hash_policy_456"},
    )

    res = stage.execute(ctx, [plan_res, policy_res])
    assert res.status == StageStatus.SUCCESS
    bundle = res.output_data["evidence_bundle"]
    assert bundle["run_id"] == "run-ev-1"
    assert bundle["topic_slug"] == "test-topic"
    assert bundle["policy_info"]["policy_decision"] == "BUILD"
    assert bundle["stage_hashes"]["execution_plan"] == "hash_plan_123"
    assert bundle["stage_hashes"]["policy_gate"] == "hash_policy_456"
