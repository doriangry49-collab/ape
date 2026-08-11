"""Unit tests for SPEC-0018 ExplainabilityStage."""

from ape.pipeline.contracts import PipelineContext, StageStatus
from ape.pipeline.stages.acquisition_execution import AcquisitionExecutionStage
from ape.pipeline.stages.capability_validation import CapabilityValidationStage
from ape.pipeline.stages.evidence_fusion import EvidenceFusionStage
from ape.pipeline.stages.explainability import ExplainabilityStage
from ape.pipeline.stages.research_plan import ResearchPlanStage
from ape.pipeline.stages.source_selection import SourceSelectionStage


def test_explainability_stage_success():
    plan_stage = ResearchPlanStage()
    select_stage = SourceSelectionStage()
    acq_stage = AcquisitionExecutionStage(offline=True)
    val_stage = CapabilityValidationStage()
    fusion_stage = EvidenceFusionStage()
    explain_stage = ExplainabilityStage()

    ctx = PipelineContext(topic_slug="Distributed Cache Engine", run_id="run-exp-1")
    plan_res = plan_stage.execute(ctx, [])
    select_res = select_stage.execute(ctx, [plan_res])
    acq_res = acq_stage.execute(ctx, [plan_res, select_res])
    val_res = val_stage.execute(ctx, [plan_res, select_res, acq_res])
    fusion_res = fusion_stage.execute(ctx, [plan_res, select_res, acq_res, val_res])
    explain_res = explain_stage.execute(ctx, [plan_res, select_res, acq_res, val_res, fusion_res])

    assert explain_res.status == StageStatus.SUCCESS
    assert explain_res.stage_name == "explainability"
    assert "summary" in explain_res.output_data
    assert len(explain_res.output_data["decision_path"]) == 2
    assert len(explain_res.output_data["evidence_path"]) == 2
    assert "confidence_reasoning" in explain_res.output_data
    assert explain_res.evidence["narrative_composed"] is True
