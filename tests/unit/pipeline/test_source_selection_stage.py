"""Unit tests for SPEC-0018 SourceSelectionStage."""

import pytest
from ape.pipeline.contracts import PipelineContext, StageResult, StageStatus
from ape.pipeline.stages.research_plan import ResearchPlanStage
from ape.pipeline.stages.source_selection import SourceSelectionStage


def test_source_selection_stage_standalone():
    stage = SourceSelectionStage()
    assert stage.name == "source_selection"

    ctx = PipelineContext(topic_slug="Cloud Cost Optimizer", run_id="run-src-1")
    result = stage.execute(ctx, [])

    assert result.status == StageStatus.SUCCESS
    assert result.stage_name == "source_selection"
    assert result.output_data["topic"] == "Cloud Cost Optimizer"
    assert "HackerNews" in result.output_data["selected_sources"]
    assert result.output_data["estimated_cost"] == "low"
    assert result.evidence["source_count"] >= 1


def test_source_selection_stage_consuming_plan_stage():
    plan_stage = ResearchPlanStage()
    select_stage = SourceSelectionStage()

    ctx = PipelineContext(topic_slug="Kubernetes Monitoring", run_id="run-src-2")
    plan_res = plan_stage.execute(ctx, [])
    select_res = select_stage.execute(ctx, [plan_res])

    assert select_res.status == StageStatus.SUCCESS
    assert select_res.output_data["priority_source"] == "HackerNews"
    assert "reasoning" in select_res.evidence
