"""Unit tests for VerificationStage."""

from pathlib import Path

from ape.pipeline.contracts import ExecutionContext, StageResult, StageStatus
from ape.pipeline.stages.verification import VerificationStage


def test_verification_stage_success(tmp_path: Path):
    # Create test deliverable file
    (tmp_path / "app.py").write_text("print('hello')", encoding="utf-8")

    stage = VerificationStage(project_root=tmp_path)
    ctx = ExecutionContext(run_id="run-ver-1", topic_slug="test-topic", dry_run=False)

    plan_result = StageResult(
        stage_name="execution_plan",
        status=StageStatus.SUCCESS,
        output_data={
            "tasks": [
                {"task_id": "t1", "deliverables": ["app.py"]},
            ]
        },
    )

    res = stage.execute(ctx, [plan_result])
    assert res.status == StageStatus.SUCCESS
    assert res.output_data["verification_passed"] is True
    assert res.output_data["verified_deliverables"] == ["app.py"]


def test_verification_stage_missing_deliverable_failed(tmp_path: Path):
    stage = VerificationStage(project_root=tmp_path)
    ctx = ExecutionContext(run_id="run-ver-2", topic_slug="test-topic", dry_run=False)

    plan_result = StageResult(
        stage_name="execution_plan",
        status=StageStatus.SUCCESS,
        output_data={
            "tasks": [
                {"task_id": "t1", "deliverables": ["missing_file.py"]},
            ]
        },
    )

    res = stage.execute(ctx, [plan_result])
    assert res.status == StageStatus.FAILED
    assert res.output_data["verification_passed"] is False
    assert res.output_data["missing_deliverables"] == ["missing_file.py"]
    assert res.evidence["failure_reason"] == "MISSING_DELIVERABLES"


def test_verification_stage_empty_file_failed(tmp_path: Path):
    # Create an empty file (0-byte) as deliverable
    (tmp_path / "empty.txt").write_text("", encoding="utf-8")

    stage = VerificationStage(project_root=tmp_path)
    ctx = ExecutionContext(run_id="run-ver-3", topic_slug="test-topic", dry_run=False)

    plan_result = StageResult(
        stage_name="execution_plan",
        status=StageStatus.SUCCESS,
        output_data={
            "tasks": [
                {"task_id": "t1", "deliverables": ["empty.txt"]},
            ]
        },
    )

    res = stage.execute(ctx, [plan_result])
    assert res.status == StageStatus.FAILED
    assert res.output_data["verification_passed"] is False
    assert res.evidence["failure_reason"] == "EMPTY_DELIVERABLES"
    assert "failure_details" in res.evidence


def test_verification_stage_invalid_json_failed(tmp_path: Path):
    # Create a .json file with invalid syntax as deliverable
    (tmp_path / "broken.json").write_text("{invalid json, missing quotes}", encoding="utf-8")

    stage = VerificationStage(project_root=tmp_path)
    ctx = ExecutionContext(run_id="run-ver-4", topic_slug="test-topic", dry_run=False)

    plan_result = StageResult(
        stage_name="execution_plan",
        status=StageStatus.SUCCESS,
        output_data={
            "tasks": [
                {"task_id": "t1", "deliverables": ["broken.json"]},
            ]
        },
    )

    res = stage.execute(ctx, [plan_result])
    assert res.status == StageStatus.FAILED
    assert res.output_data["verification_passed"] is False
    assert res.evidence["failure_reason"] == "INVALID_JSON_DELIVERABLES"
    assert "failure_details" in res.evidence
