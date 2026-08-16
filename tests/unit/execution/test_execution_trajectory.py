from pathlib import Path

from ape.intelligence.execution.trajectory import ExecutionTrajectory, TrajectoryStep
from ape.pipeline.contracts import ExecutionContext, StageStatus
from ape.pipeline.stages.task_execution import TaskExecutionStage


def test_trajectory_step_serialization():
    step = TrajectoryStep(
        step_id="step_t1_1",
        task_id="t1",
        attempt=1,
        thought="Creating test file",
        action="create_file",
        params={"path": "test.txt"},
        exit_code=0,
        stdout_hash="a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
        stderr_signature="",
        status="EXECUTED",
        timestamp="2026-08-11T20:00:00Z",
    )

    d = step.to_dict()
    assert d["step_id"] == "step_t1_1"
    assert d["task_id"] == "t1"
    assert d["action"] == "create_file"

    rehydrated = TrajectoryStep.from_dict(d)
    assert rehydrated.step_id == step.step_id
    assert rehydrated.params == step.params


def test_execution_trajectory_merkle_hash_binding():
    trajectory = ExecutionTrajectory(
        execution_id="exec_test",
        topic_slug="test_topic",
        decision_id="DEC_001",
        policy_decision="BUILD",
    )

    # Empty trajectory digest matches standard empty string SHA-256
    empty_hash = trajectory.compute_trajectory_hash()
    assert len(empty_hash) == 64

    step1 = TrajectoryStep(
        step_id="s1",
        task_id="t1",
        attempt=1,
        thought="t1",
        action="create_file",
        params={},
        exit_code=0,
        stdout_hash="h1",
        stderr_signature="",
        status="EXECUTED",
        timestamp="2026-08-11T20:00:00Z",
    )
    trajectory.append_step(step1)
    hash1 = trajectory.compute_trajectory_hash()
    assert hash1 != empty_hash

    step2 = TrajectoryStep(
        step_id="s2",
        task_id="t2",
        attempt=1,
        thought="t2",
        action="modify_file",
        params={},
        exit_code=0,
        stdout_hash="h2",
        stderr_signature="",
        status="EXECUTED",
        timestamp="2026-08-11T20:01:00Z",
    )
    trajectory.append_step(step2)
    hash2 = trajectory.compute_trajectory_hash()
    assert hash2 != hash1

    # Tamper detection: modifying a step alters trajectory hash
    step1.action = "delete_file"
    assert trajectory.compute_trajectory_hash() != hash2


def test_execution_trajectory_task_filter():
    trajectory = ExecutionTrajectory(execution_id="exec_1", topic_slug="slug_1")
    s1 = TrajectoryStep("s1", "t1", 1, "", "act", {}, 0, "h", "", "EXECUTED", "")
    s2 = TrajectoryStep("s2", "t2", 1, "", "act", {}, 0, "h", "", "EXECUTED", "")
    s3 = TrajectoryStep("s3", "t1", 2, "", "act", {}, 0, "h", "", "EXECUTED", "")

    trajectory.append_step(s1)
    trajectory.append_step(s2)
    trajectory.append_step(s3)

    t1_steps = trajectory.get_steps_for_task("t1")
    assert len(t1_steps) == 2
    assert [s.step_id for s in t1_steps] == ["s1", "s3"]


def test_task_execution_stage_trajectory_output(tmp_path: Path):
    stage = TaskExecutionStage(project_root=tmp_path)
    context = ExecutionContext(run_id="run_100", topic_slug="test_trajectory", dry_run=True)

    prev_results = []
    result = stage.execute(context, prev_results)

    assert result.status == StageStatus.SUCCESS
    assert "trajectory" in result.output_data
    traj_dict = result.output_data["trajectory"]
    assert traj_dict["topic_slug"] == "test_trajectory"
    assert "trajectory_hash" in traj_dict
    assert "trajectory_hash" in result.evidence
