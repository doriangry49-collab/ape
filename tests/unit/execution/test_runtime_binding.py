from pathlib import Path

import pytest

from ape.intelligence.execution.evaluators import ExecutionHealthSignal, SignalSeverity
from ape.pipeline.contracts import ExecutionContext, StageStatus
from ape.pipeline.runner import ConstitutionalPipelineRunner, PipelineExecutionError
from ape.pipeline.stages.task_execution import TaskExecutionStage


def test_runtime_binding_safe_hold_blocks_stage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    stage = TaskExecutionStage(project_root=tmp_path)
    context = ExecutionContext(run_id="run_binding_1", topic_slug="test_safe_hold", dry_run=True)

    # Inject CRITICAL signal to force SAFE_HOLD intervention proposal
    def mock_evaluate(self, trajectory):
        return [
            ExecutionHealthSignal(
                signal_type="REPEATED_ERROR",
                severity=SignalSeverity.CRITICAL,
                confidence=1.0,
                signature="err_sig_crit",
                task_id="t1",
                evidence_ref="s1",
                message="Critical error loop detected",
            )
        ]

    from ape.intelligence.execution.evaluators import CompositeRuntimeEvaluator
    monkeypatch.setattr(CompositeRuntimeEvaluator, "evaluate", mock_evaluate)

    result = stage.execute(context, [])

    # Verify SAFE_HOLD maps directly to StageStatus.BLOCKED
    assert result.status == StageStatus.BLOCKED
    assert "Critical execution risk detected" in result.error
    assert result.output_data["intervention_proposal"]["proposed_action"] == "SAFE_HOLD"


def test_runtime_binding_runner_halts_on_safe_hold(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = ConstitutionalPipelineRunner()
    stage = TaskExecutionStage(project_root=tmp_path)
    runner.add_stage(stage)
    context = ExecutionContext(run_id="run_binding_2", topic_slug="test_runner_halt", dry_run=True)

    # Inject CRITICAL signal to force SAFE_HOLD intervention proposal
    def mock_evaluate(self, trajectory):
        return [
            ExecutionHealthSignal(
                signal_type="REPEATED_ERROR",
                severity=SignalSeverity.CRITICAL,
                confidence=1.0,
                signature="err_sig_crit",
                task_id="t1",
                evidence_ref="s1",
                message="Critical error loop detected",
            )
        ]

    from ape.intelligence.execution.evaluators import CompositeRuntimeEvaluator
    monkeypatch.setattr(CompositeRuntimeEvaluator, "evaluate", mock_evaluate)

    # Verify ConstitutionalPipelineRunner raises PipelineExecutionError when stage status is BLOCKED
    with pytest.raises(PipelineExecutionError) as exc_info:
        runner.run(context)

    assert "halted at stage 'task_execution'" in str(exc_info.value)
    assert exc_info.value.stage_result.status == StageStatus.BLOCKED
