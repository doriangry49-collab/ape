"""Unit tests for ExecutionPersistStage."""

from pathlib import Path
import pytest

from ape.pipeline.contracts import ExecutionContext, StageResult, StageStatus
from ape.pipeline.stages.execution_persist import ExecutionPersistStage


def test_execution_persist_stage_success(tmp_path: Path):
    stage = ExecutionPersistStage(project_root=tmp_path)
    ctx = ExecutionContext(run_id="run-pst-1", topic_slug="test-topic", dry_run=False)

    exec_result = StageResult(
        stage_name="task_execution",
        status=StageStatus.SUCCESS,
        output_data={
            "state": {
                "execution_id": "ex_100",
                "topic": "test-topic",
                "tasks": [],
                "status": "COMPLETED",
            }
        },
    )
    ev_result = StageResult(
        stage_name="execution_evidence",
        status=StageStatus.SUCCESS,
        output_data={"evidence_bundle": {"run_id": "run-pst-1"}},
    )

    res = stage.execute(ctx, [exec_result, ev_result])
    assert res.status == StageStatus.SUCCESS
    assert res.output_data["persist_receipt"]["state_updated"] is True
    assert res.output_data["persist_receipt"]["audit_appended"] is True

    # Verify disk file creation
    state_file = tmp_path / ".build" / "execution" / "test-topic" / "current.json"
    assert state_file.exists()
