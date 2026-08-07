"""Unit tests for SPEC-0018 ResearchPlanStage."""

import pytest
from ape.pipeline.contracts import PipelineContext, StageStatus
from ape.pipeline.stages.research_plan import ResearchPlanStage


def test_research_plan_stage_success():
    stage = ResearchPlanStage()
    assert stage.name == "research_plan"

    ctx = PipelineContext(topic_slug="AI Bookkeeping SaaS", run_id="run-plan-1")
    result = stage.execute(ctx, [])

    assert result.status == StageStatus.SUCCESS
    assert result.stage_name == "research_plan"
    assert result.output_data["topic"] == "AI Bookkeeping SaaS"
    assert result.output_data["clean_topic_id"] == "aibookke"
    assert len(result.output_data["search_queries"]) == 3
    assert result.evidence["query_count"] == 3


def test_research_plan_stage_empty_topic_failure():
    stage = ResearchPlanStage()
    ctx = PipelineContext(topic_slug="   ", run_id="run-plan-err")
    result = stage.execute(ctx, [])

    assert result.status == StageStatus.FAILED
    assert "cannot be empty" in result.error
