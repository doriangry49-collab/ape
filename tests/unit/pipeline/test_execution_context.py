"""Unit tests for BasePipelineContext, ResearchContext, and ExecutionContext."""

import pytest
from ape.pipeline.contracts import (
    BasePipelineContext,
    ExecutionContext,
    ResearchContext,
)


def test_base_pipeline_context_immutability():
    ctx = BasePipelineContext(run_id="run-base-1", resource_budget={"max_steps": 10})
    assert ctx.run_id == "run-base-1"
    assert ctx.resource_budget == {"max_steps": 10}

    with pytest.raises(AttributeError):
        ctx.run_id = "run-base-2"  # type: ignore


def test_research_context_with_updates():
    ctx = ResearchContext(run_id="run-res-1", topic_slug="ai-agent")
    updated = ctx.with_updates(topic_slug="ai-agent-v2", metadata={"key": "val"})

    assert ctx.topic_slug == "ai-agent"
    assert updated.topic_slug == "ai-agent-v2"
    assert updated.metadata == {"key": "val"}
    assert updated.run_id == "run-res-1"


def test_execution_context_typed_fields_and_updates():
    ctx = ExecutionContext(
        run_id="exec-run-100",
        topic_slug="payment-gateway",
        topic="Payment Gateway Integration",
        dry_run=True,
        auto_deny_approvals=False,
    )

    assert ctx.topic == "Payment Gateway Integration"
    assert ctx.dry_run is True
    assert ctx.auto_deny_approvals is False

    updated = ctx.with_updates(dry_run=False, auto_deny_approvals=True)
    assert ctx.dry_run is True  # Immutability preserved
    assert updated.dry_run is False
    assert updated.auto_deny_approvals is True
    assert updated.topic_slug == "payment-gateway"
