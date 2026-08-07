"""Unit tests for CapabilityCheckStage."""

from pathlib import Path
import pytest

from ape.pipeline.contracts import ExecutionContext, StageResult, StageStatus
from ape.pipeline.stages.capability_check import (
    CapabilityCheckStage,
    CapabilityProvider,
)


def test_capability_check_stage_dry_run_success(tmp_path: Path):
    stage = CapabilityCheckStage(project_root=tmp_path)
    ctx = ExecutionContext(run_id="run-cap-1", topic_slug="test-topic", dry_run=True)

    plan_result = StageResult(
        stage_name="execution_plan",
        status=StageStatus.SUCCESS,
        output_data={
            "tasks": [
                {"task_id": "t1", "action": "create_file"},
            ]
        },
    )

    res = stage.execute(ctx, [plan_result])
    assert res.status == StageStatus.SUCCESS
    assert res.output_data["execution_backend"] == "simulation"
    assert res.output_data["execution_mode"] == "dry_run"
    assert res.output_data["capabilities_satisfied"] is True
    assert "environment_snapshot" in res.output_data
    assert res.output_data["environment_snapshot"]["backend"] == "simulation"


def test_capability_check_stage_missing_capability_blocked(tmp_path: Path):
    class MockProvider(CapabilityProvider):
        def collect(self, tasks, dry_run=True):
            return {
                "required_capabilities": ["docker", "filesystem"],
                "resolved_capabilities": ["filesystem"],
                "missing_capabilities": ["docker"],
                "execution_backend": "docker",
                "execution_mode": "live",
                "environment_snapshot": {
                    "backend": "docker",
                    "mode": "live",
                    "capabilities": {"docker": False, "filesystem": True},
                    "platform": {"os": "linux", "sandbox": "local"},
                },
            }

    stage = CapabilityCheckStage(project_root=tmp_path, provider=MockProvider())
    ctx = ExecutionContext(run_id="run-cap-2", topic_slug="test-topic", dry_run=False)

    res = stage.execute(ctx, [])
    assert res.status == StageStatus.BLOCKED
    assert res.output_data["missing_capabilities"] == ["docker"]
    assert res.evidence["blocked_reason"]["code"] == "MISSING_CAPABILITY"
    assert res.evidence["blocked_reason"]["retryable"] is True
    assert "Execution BLOCKED" in (res.error or "")
