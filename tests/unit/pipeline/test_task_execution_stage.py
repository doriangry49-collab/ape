"""Unit tests for TaskExecutionStage."""

from pathlib import Path

from ape.pipeline.contracts import ExecutionContext, StageResult, StageStatus
from ape.pipeline.stages.task_execution import TaskExecutionStage


def test_task_execution_stage_success(tmp_path: Path):
    stage = TaskExecutionStage(project_root=tmp_path)
    ctx = ExecutionContext(run_id="run-exec-1", topic_slug="test-topic", dry_run=True)

    plan_result = StageResult(
        stage_name="execution_plan",
        status=StageStatus.SUCCESS,
        output_data={
            "tasks": [
                {
                    "task_id": "task_100",
                    "description": "Create sample file",
                    "deliverables": ["sample.py"],
                    "action": "create_file",
                }
            ]
        },
    )
    cap_result = StageResult(
        stage_name="capability_check",
        status=StageStatus.SUCCESS,
        output_data={"execution_backend": "simulation"},
    )

    res = stage.execute(ctx, [plan_result, cap_result])
    assert res.status == StageStatus.SUCCESS
    assert res.output_data["execution_summary"]["executed"] == ["task_100"]
    assert res.output_data["tasks_executed_count"] == 1


def test_task_execution_stage_path_traversal_rejection(tmp_path: Path):
    stage = TaskExecutionStage(project_root=tmp_path)
    ctx = ExecutionContext(run_id="run-exec-2", topic_slug="test-topic", dry_run=True)

    plan_result = StageResult(
        stage_name="execution_plan",
        status=StageStatus.SUCCESS,
        output_data={
            "tasks": [
                {
                    "task_id": "task_bad",
                    "description": "Malicious file creation",
                    "deliverables": ["../../etc/passwd"],
                    "action": "create_file",
                }
            ]
        },
    )

    res = stage.execute(ctx, [plan_result])
    assert res.status == StageStatus.FAILED
    assert "Path containment rejected" in (res.error or "")


def test_task_execution_stage_keyboard_interrupt(tmp_path: Path):
    stage = TaskExecutionStage(project_root=tmp_path)
    ctx = ExecutionContext(
        run_id="run-exec-3",
        topic_slug="test-topic",
        dry_run=True,
        interrupt_after_tasks=1,
    )

    plan_result = StageResult(
        stage_name="execution_plan",
        status=StageStatus.SUCCESS,
        output_data={
            "tasks": [
                {"task_id": "t1", "description": "T1", "deliverables": ["t1.txt"], "action": "create_file"},
                {"task_id": "t2", "description": "T2", "deliverables": ["t2.txt"], "action": "create_file"},
            ]
        },
    )

    res = stage.execute(ctx, [plan_result])
    assert res.status == StageStatus.BLOCKED
    assert res.evidence["failure_reason"] == "KEYBOARD_INTERRUPT"
