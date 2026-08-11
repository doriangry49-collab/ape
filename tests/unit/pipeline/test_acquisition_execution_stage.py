"""Unit tests for SPEC-0018 AcquisitionExecutionStage."""

from ape.pipeline.contracts import PipelineContext, StageStatus
from ape.pipeline.stages.acquisition_execution import AcquisitionExecutionStage
from ape.pipeline.stages.research_plan import ResearchPlanStage
from ape.pipeline.stages.source_selection import SourceSelectionStage


def test_acquisition_execution_stage_offline():
    plan_stage = ResearchPlanStage()
    select_stage = SourceSelectionStage()
    acq_stage = AcquisitionExecutionStage(offline=True)

    ctx = PipelineContext(topic_slug="SaaS Billing Engine", run_id="run-acq-1")
    plan_res = plan_stage.execute(ctx, [])
    select_res = select_stage.execute(ctx, [plan_res])
    acq_res = acq_stage.execute(ctx, [plan_res, select_res])

    assert acq_res.status == StageStatus.SUCCESS
    assert acq_res.stage_name == "acquisition_execution"
    assert acq_res.output_data["observation_count"] == 2
    assert acq_res.evidence["successful_acquisitions"] == 2
    assert "combined_signals" in acq_res.output_data
