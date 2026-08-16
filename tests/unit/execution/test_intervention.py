"""
Unit & Integration Tests for Governed Adaptive Intervention Policy — ORION-124 (Mission C).
Verifies GovernedInterventionPolicy and TaskExecutionStage output propagation.
"""

from pathlib import Path

from ape.intelligence.execution.evaluators import ExecutionHealthSignal, SignalSeverity
from ape.intelligence.execution.intervention import (
    GovernedInterventionPolicy,
    InterventionAction,
)
from ape.pipeline.contracts import ExecutionContext, StageStatus
from ape.pipeline.stages.task_execution import TaskExecutionStage


def test_intervention_nominal_execution():
    policy = GovernedInterventionPolicy()
    proposal = policy.resolve([])

    assert proposal.proposed_action == InterventionAction.CONTINUE
    assert proposal.severity == SignalSeverity.LOW
    assert "nominal" in proposal.reason.lower()


def test_intervention_critical_signal_safe_hold():
    policy = GovernedInterventionPolicy()
    crit_sig = ExecutionHealthSignal(
        signal_type="REPEATED_ERROR",
        severity=SignalSeverity.CRITICAL,
        confidence=1.0,
        signature="err_sig_123",
        task_id="t1",
        evidence_ref="s3",
        message="Repeated error signature detected",
    )

    proposal = policy.resolve([crit_sig])
    assert proposal.proposed_action == InterventionAction.SAFE_HOLD
    assert proposal.severity == SignalSeverity.CRITICAL
    assert proposal.evidence_ref == "s3"
    assert "Critical execution risk" in proposal.reason


def test_intervention_high_signal_retry_and_exhaustion():
    policy = GovernedInterventionPolicy()
    high_sig = ExecutionHealthSignal(
        signal_type="ACTION_LOOP",
        severity=SignalSeverity.HIGH,
        confidence=1.0,
        signature="loop_sig_456",
        task_id="t1",
        evidence_ref="s4",
        message="Action loop detected",
    )

    # 1. Under retry limit -> Action RETRY
    proposal1 = policy.resolve([high_sig], current_retry_count=0, max_retries=1)
    assert proposal1.proposed_action == InterventionAction.RETRY
    assert proposal1.severity == SignalSeverity.HIGH

    # 2. Retry limit exhausted -> Action SAFE_HOLD
    proposal2 = policy.resolve([high_sig], current_retry_count=1, max_retries=1)
    assert proposal2.proposed_action == InterventionAction.SAFE_HOLD
    assert proposal2.severity == SignalSeverity.HIGH


def test_intervention_medium_signal_continue():
    policy = GovernedInterventionPolicy()
    med_sig = ExecutionHealthSignal(
        signal_type="NO_PROGRESS",
        severity=SignalSeverity.MEDIUM,
        confidence=1.0,
        signature="stagnation_3_steps",
        task_id="t1",
        evidence_ref="s3",
        message="Stagnation detected",
    )

    proposal = policy.resolve([med_sig])
    assert proposal.proposed_action == InterventionAction.CONTINUE
    assert proposal.severity == SignalSeverity.MEDIUM


def test_evaluator_module_boundary_isolation():
    """Verify that evaluators module contains zero references to InterventionAction."""
    import ape.intelligence.execution.evaluators as eval_module
    assert not hasattr(eval_module, "InterventionAction")
    assert not hasattr(eval_module, "GovernedInterventionPolicy")


def test_task_execution_stage_intervention_output(tmp_path: Path):
    stage = TaskExecutionStage(project_root=tmp_path)
    context = ExecutionContext(run_id="run_100", topic_slug="test_intervention", dry_run=True)

    prev_results = []
    result = stage.execute(context, prev_results)

    assert result.status == StageStatus.SUCCESS
    assert "intervention_proposal" in result.output_data
    assert "intervention_action" in result.evidence
    prop_dict = result.output_data["intervention_proposal"]
    assert prop_dict["proposed_action"] == "CONTINUE"
