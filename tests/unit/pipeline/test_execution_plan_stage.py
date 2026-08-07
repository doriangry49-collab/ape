"""Unit tests for ExecutionPlanStage."""

import json
from pathlib import Path
import pytest

from ape.pipeline.contracts import ExecutionContext, StageStatus
from ape.pipeline.stages.execution_plan import ExecutionPlanStage


def test_execution_plan_stage_success(tmp_path: Path):
    # Setup test workspace with a valid roadmap
    roadmaps_dir = tmp_path / ".build" / "roadmaps"
    roadmaps_dir.mkdir(parents=True, exist_ok=True)
    roadmap_data = {
        "roadmap_id": "rm_test_123",
        "milestones": [
            {
                "tasks": [
                    {
                        "task_id": "task_1",
                        "description": "Create main.py file",
                        "deliverables": ["main.py"],
                        "action": "create_file",
                    },
                    {
                        "task_id": "task_2",
                        "description": "Run unit tests",
                        "deliverables": [],
                        "action": "run_tests",
                    },
                ]
            }
        ],
    }
    (roadmaps_dir / "test-topic.json").write_text(
        json.dumps(roadmap_data), encoding="utf-8"
    )

    stage = ExecutionPlanStage(project_root=tmp_path)
    ctx = ExecutionContext(
        run_id="run-exec-plan-1",
        topic_slug="test-topic",
        topic="Test Topic",
    )

    res = stage.execute(ctx, [])
    assert res.status == StageStatus.SUCCESS
    assert res.output_data["execution_plan"]["roadmap_id"] == "rm_test_123"
    assert res.output_data["execution_plan"]["task_count"] == 2
    assert res.output_data["execution_plan"]["task_ids"] == ["task_1", "task_2"]
    assert res.output_data["execution_plan"]["state_exists"] is False


def test_execution_plan_stage_missing_roadmap(tmp_path: Path):
    stage = ExecutionPlanStage(project_root=tmp_path)
    ctx = ExecutionContext(
        run_id="run-exec-plan-2",
        topic_slug="non-existent-topic",
    )

    res = stage.execute(ctx, [])
    assert res.status == StageStatus.FAILED
    assert "Roadmap not found" in (res.error or "")


def test_execution_plan_stage_zero_tasks_fails(tmp_path: Path):
    roadmaps_dir = tmp_path / ".build" / "roadmaps"
    roadmaps_dir.mkdir(parents=True, exist_ok=True)
    roadmap_data = {
        "roadmap_id": "rm_empty",
        "milestones": [{"tasks": []}],
    }
    (roadmaps_dir / "empty-topic.json").write_text(
        json.dumps(roadmap_data), encoding="utf-8"
    )

    stage = ExecutionPlanStage(project_root=tmp_path)
    ctx = ExecutionContext(
        run_id="run-exec-plan-3",
        topic_slug="empty-topic",
    )

    res = stage.execute(ctx, [])
    assert res.status == StageStatus.FAILED
    assert "zero executable tasks" in (res.error or "")
