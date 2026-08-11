"""Unit tests for ReleaseDecisionStage."""


from ape.pipeline.contracts import BasePipelineContext, StageResult, StageStatus
from ape.pipeline.stages.release_decision import ReleaseDecisionStage


def test_release_decision_stage_approved():
    stage = ReleaseDecisionStage()
    ctx = BasePipelineContext(run_id="run-rel-1")

    ver_res = StageResult(
        stage_name="verification",
        status=StageStatus.SUCCESS,
        output_data={"verification_passed": True},
    )
    pst_res = StageResult(
        stage_name="execution_persist",
        status=StageStatus.SUCCESS,
        output_data={"persist_receipt": {"state_updated": True, "audit_appended": True}},
    )

    res = stage.execute(ctx, [ver_res, pst_res])
    assert res.status == StageStatus.SUCCESS
    assert res.output_data["release_decision"]["status"] == "APPROVED"
    assert res.output_data["released"] is True


def test_release_decision_stage_rejected_on_prior_failure():
    stage = ReleaseDecisionStage()
    ctx = BasePipelineContext(run_id="run-rel-2")

    fail_res = StageResult(
        stage_name="task_execution",
        status=StageStatus.FAILED,
        error="Execution error",
    )

    res = stage.execute(ctx, [fail_res])
    assert res.status == StageStatus.FAILED
    assert res.output_data["release_decision"]["status"] == "REJECTED"
    assert res.output_data["release_decision"]["failed_stage"] == "task_execution"
