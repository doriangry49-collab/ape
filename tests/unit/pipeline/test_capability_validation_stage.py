"""Unit tests for SPEC-0018 CapabilityValidationStage (SPEC-0012)."""

import pytest
from ape.pipeline.contracts import PipelineContext, StageResult, StageStatus
from ape.pipeline.stages.acquisition_execution import AcquisitionExecutionStage
from ape.pipeline.stages.capability_validation import CapabilityValidationStage
from ape.pipeline.stages.research_plan import ResearchPlanStage
from ape.pipeline.stages.source_selection import SourceSelectionStage


def test_capability_validation_stage_success():
    plan_stage = ResearchPlanStage()
    select_stage = SourceSelectionStage()
    acq_stage = AcquisitionExecutionStage(offline=True)
    val_stage = CapabilityValidationStage()

    ctx = PipelineContext(topic_slug="Serverless Database", run_id="run-val-1")
    plan_res = plan_stage.execute(ctx, [])
    select_res = select_stage.execute(ctx, [plan_res])
    acq_res = acq_stage.execute(ctx, [plan_res, select_res])
    val_res = val_stage.execute(ctx, [plan_res, select_res, acq_res])

    assert val_res.status == StageStatus.SUCCESS
    assert val_res.stage_name == "capability_validation"
    assert val_res.output_data["spec_0012_compliant"] is True
    assert val_res.output_data["validated_count"] == 2
    assert val_res.evidence["synthetic_mock_emitted"] is False


def test_capability_validation_stage_handles_error_observations():
    val_stage = CapabilityValidationStage()
    ctx = PipelineContext(topic_slug="Error Topic", run_id="run-val-2")

    fake_acq_res = StageResult(
        stage_name="acquisition_execution",
        status=StageStatus.SUCCESS,
        output_data={
            "raw_observations": [
                {"source": "HackerNews", "status": "ERROR", "error": "NetworkTimeout"},
                {"source": "AudienceHeuristics", "status": "SUCCESS", "signals": {"confidence": 0.8}},
            ]
        },
    )

    val_res = val_stage.execute(ctx, [fake_acq_res])
    assert val_res.status == StageStatus.SUCCESS
    assert val_res.output_data["invalid_count"] == 1
    assert val_res.output_data["validated_observations"][0]["synthetic"] is False
    assert val_res.output_data["validated_observations"][0]["error_reason"] == "NetworkTimeout"
