"""Unit tests for SPEC-0018 Constitutional Pipeline Core Contracts & Runner."""

import pytest

from ape.pipeline.contracts import (
    PipelineContext,
    PipelineStage,
    StageResult,
    StageStatus,
)
from ape.pipeline.runner import ConstitutionalPipelineRunner, PipelineExecutionError


class DummySuccessStage(PipelineStage):
    def __init__(self, stage_name: str = "dummy_success"):
        self._name = stage_name

    @property
    def name(self) -> str:
        return self._name

    def execute(self, context: PipelineContext, previous_results: list[StageResult]) -> StageResult:
        return StageResult(
            stage_name=self.name,
            status=StageStatus.SUCCESS,
            output_data={"message": f"hello from {self.name}"},
            evidence={"step": len(previous_results) + 1},
        )


class DummyFailStage(PipelineStage):
    @property
    def name(self) -> str:
        return "dummy_fail"

    def execute(self, context: PipelineContext, previous_results: list[StageResult]) -> StageResult:
        return StageResult(
            stage_name=self.name,
            status=StageStatus.FAILED,
            error="Stage hard error",
        )


def test_pipeline_context_immutability_and_updates():
    ctx = PipelineContext(
        topic_slug="test-topic",
        run_id="run-123",
        resource_budget={"max_tokens": 1000},
        metadata={"env": "test"},
    )
    assert ctx.topic_slug == "test-topic"
    assert ctx.run_id == "run-123"

    # Strict immutability check
    with pytest.raises(AttributeError):
        ctx.topic_slug = "new-topic"

    # Controlled update check
    new_ctx = ctx.with_updates(
        resource_budget={"max_tokens": 2000, "max_cost_usd": 0.5},
        metadata={"owner": "agent"},
    )
    assert new_ctx is not ctx
    assert new_ctx.topic_slug == "test-topic"
    assert new_ctx.resource_budget["max_tokens"] == 2000
    assert new_ctx.resource_budget["max_cost_usd"] == 0.5
    assert new_ctx.metadata["env"] == "test"
    assert new_ctx.metadata["owner"] == "agent"


def test_merkle_lineage_chaining():
    stage1 = DummySuccessStage("stage_1")
    stage2 = DummySuccessStage("stage_2")
    runner = ConstitutionalPipelineRunner([stage1, stage2])

    ctx = PipelineContext(topic_slug="merkle-test", run_id="merkle-run-1")
    results = runner.run(ctx)

    assert len(results) == 2
    # Stage 1 parent_hash is None
    assert results[0].parent_hash is None
    assert results[0].evidence["parent_hash"] is None
    hash1 = results[0].evidence["stage_hash"]

    # Stage 2 parent_hash MUST equal Stage 1's stage_hash
    assert results[1].parent_hash == hash1
    assert results[1].evidence["parent_hash"] == hash1
    assert results[1].evidence["stage_hash"] != hash1


def test_pipeline_runner_fail_closed():
    runner = ConstitutionalPipelineRunner([DummySuccessStage("s1"), DummyFailStage(), DummySuccessStage("s3")])
    ctx = PipelineContext(topic_slug="fail-topic", run_id="run-666")

    with pytest.raises(PipelineExecutionError) as exc_info:
        runner.run(ctx)

    assert "dummy_fail" in str(exc_info.value)
    assert exc_info.value.stage_result.status == StageStatus.FAILED
