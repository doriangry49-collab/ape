"""
Unit & Integration Tests for Deterministic Runtime Evaluators — ORION-123 (Mission B).
Verifies RepeatedErrorEvaluator, LoopEvaluator, ProgressEvaluator, BudgetBurnEvaluator,
CompositeRuntimeEvaluator, and TaskExecutionStage output propagation.
"""

from pathlib import Path

from ape.intelligence.execution.evaluators import (
    BudgetBurnEvaluator,
    CompositeRuntimeEvaluator,
    LoopEvaluator,
    ProgressEvaluator,
    RepeatedErrorEvaluator,
    SignalSeverity,
)
from ape.intelligence.execution.trajectory import ExecutionTrajectory, TrajectoryStep
from ape.pipeline.contracts import ExecutionContext, StageStatus
from ape.pipeline.stages.task_execution import TaskExecutionStage


def _step(
    step_id: str,
    task_id: str,
    attempt: int,
    act: str,
    err: str = "",
    status: str = "EXECUTED",
    ts: str = "",
) -> TrajectoryStep:
    return TrajectoryStep(
        step_id=step_id,
        task_id=task_id,
        attempt=attempt,
        thought="test",
        action=act,
        params={"p": "v"},
        exit_code=1 if err else 0,
        stdout_hash="h_test",
        stderr_signature=err,
        status=status,
        timestamp=ts,
    )


def test_repeated_error_evaluator():
    trajectory = ExecutionTrajectory(execution_id="exec_1", topic_slug="slug_1")
    evaluator = RepeatedErrorEvaluator(threshold=3)

    # 2 repeated errors -> No signal yet
    trajectory.append_step(_step("s1", "t1", 1, "act", "FileNotFoundError: missing.py", "FAILED"))
    trajectory.append_step(_step("s2", "t1", 2, "act", "FileNotFoundError: missing.py", "FAILED"))
    signals = evaluator.evaluate(trajectory)
    assert len(signals) == 0

    # 3rd repeated error -> Triggers CRITICAL REPEATED_ERROR signal
    trajectory.append_step(_step("s3", "t1", 3, "act", "FileNotFoundError: missing.py", "FAILED"))
    signals = evaluator.evaluate(trajectory)
    assert len(signals) == 1
    sig = signals[0]
    assert sig.signal_type == "REPEATED_ERROR"
    assert sig.severity == SignalSeverity.CRITICAL
    assert sig.signature == "FileNotFoundError: missing.py"
    assert sig.task_id == "t1"
    assert sig.evidence_ref == "s3"


def test_loop_evaluator_ping_pong_detection():
    trajectory = ExecutionTrajectory(execution_id="exec_1", topic_slug="slug_1")
    evaluator = LoopEvaluator()

    # Pattern A -> B -> A -> B
    trajectory.append_step(_step("s1", "t1", 1, "create_file"))
    trajectory.append_step(_step("s2", "t1", 2, "modify_file"))
    trajectory.append_step(_step("s3", "t1", 3, "create_file"))
    trajectory.append_step(_step("s4", "t1", 4, "modify_file"))

    signals = evaluator.evaluate(trajectory)
    assert len(signals) == 1
    sig = signals[0]
    assert sig.signal_type == "ACTION_LOOP"
    assert sig.severity == SignalSeverity.HIGH
    assert sig.task_id == "t1"
    assert sig.evidence_ref == "s4"


def test_progress_evaluator_stagnation():
    trajectory = ExecutionTrajectory(execution_id="exec_1", topic_slug="slug_1")
    evaluator = ProgressEvaluator(max_stagnant_steps=3)

    trajectory.append_step(_step("s1", "t1", 1, "act", "err1", "FAILED"))
    trajectory.append_step(_step("s2", "t1", 2, "act", "err2", "FAILED"))
    trajectory.append_step(_step("s3", "t1", 3, "act", "err3", "FAILED"))

    signals = evaluator.evaluate(trajectory)
    assert len(signals) == 1
    sig = signals[0]
    assert sig.signal_type == "NO_PROGRESS"
    assert sig.severity == SignalSeverity.MEDIUM


def test_budget_burn_evaluator_latency():
    trajectory = ExecutionTrajectory(execution_id="exec_1", topic_slug="slug_1")
    evaluator = BudgetBurnEvaluator(max_seconds=10.0)

    trajectory.append_step(_step("s1", "t1", 1, "act", ts="2026-08-11T20:00:00+00:00"))
    trajectory.append_step(_step("s2", "t1", 2, "act", ts="2026-08-11T20:00:20+00:00"))

    signals = evaluator.evaluate(trajectory)
    assert len(signals) == 1
    sig = signals[0]
    assert sig.signal_type == "BUDGET_WARNING"
    assert sig.severity == SignalSeverity.HIGH


def test_composite_runtime_evaluator_aggregation():
    trajectory = ExecutionTrajectory(execution_id="exec_1", topic_slug="slug_1")
    composite = CompositeRuntimeEvaluator()

    # Single clean step -> 0 signals
    step_clean = _step("s1", "t1", 1, "act", status="COMPLETED", ts="2026-08-11T20:00:00+00:00")
    trajectory.append_step(step_clean)
    signals = composite.evaluate(trajectory)
    assert len(signals) == 0


def test_task_execution_stage_health_signals_output(tmp_path: Path):
    stage = TaskExecutionStage(project_root=tmp_path)
    context = ExecutionContext(run_id="run_100", topic_slug="test_evaluators", dry_run=True)

    prev_results = []
    result = stage.execute(context, prev_results)

    assert result.status == StageStatus.SUCCESS
    assert "health_signals" in result.output_data
    assert "health_signals_count" in result.evidence
    assert isinstance(result.output_data["health_signals"], list)
