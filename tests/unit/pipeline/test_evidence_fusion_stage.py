"""Unit tests for SPEC-0018 EvidenceFusionStage."""

from ape.pipeline.contracts import PipelineContext, StageStatus
from ape.pipeline.stages.acquisition_execution import AcquisitionExecutionStage
from ape.pipeline.stages.capability_validation import CapabilityValidationStage
from ape.pipeline.stages.evidence_fusion import EvidenceFusionStage
from ape.pipeline.stages.research_plan import ResearchPlanStage
from ape.pipeline.stages.source_selection import SourceSelectionStage


def test_evidence_fusion_stage_success():
    plan_stage = ResearchPlanStage()
    select_stage = SourceSelectionStage()
    acq_stage = AcquisitionExecutionStage(offline=True)
    val_stage = CapabilityValidationStage()
    fusion_stage = EvidenceFusionStage()

    ctx = PipelineContext(topic_slug="API Gateway", run_id="run-fusion-1")
    plan_res = plan_stage.execute(ctx, [])
    select_res = select_stage.execute(ctx, [plan_res])
    acq_res = acq_stage.execute(ctx, [plan_res, select_res])
    val_res = val_stage.execute(ctx, [plan_res, select_res, acq_res])
    fusion_res = fusion_stage.execute(ctx, [plan_res, select_res, acq_res, val_res])

    assert fusion_res.status == StageStatus.SUCCESS
    assert fusion_res.stage_name == "evidence_fusion"
    assert fusion_res.output_data["verified_observations_count"] == 3
    assert fusion_res.output_data["agreement_score"] > 0.0
    assert fusion_res.evidence["synthetic"] is False
