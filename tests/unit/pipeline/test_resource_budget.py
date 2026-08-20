"""SPEC-0019 Resource Budget Model — Unit Tests (ORION-159).

Tests ResourceBudget, ResourceUsage, ResourceBudgetExceededError, budget profiles,
ConstitutionalPipelineRunner pre-stage enforcement, and governance evidence emission.

Phase 1 honesty contract: passive dimensions are tested to confirm they do NOT
accidentally enforce when their telemetry is absent (always-zero/empty).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, call, patch

import pytest

from ape.pipeline.contracts import BasePipelineContext, PipelineStage, StageResult, StageStatus
from ape.pipeline.resource_budget import (
    DEFAULT_EXECUTION_BUDGET,
    DEFAULT_RESEARCH_BUDGET,
    STRICT_CI_BUDGET,
    ResourceBudget,
    ResourceBudgetExceededError,
    ResourceUsage,
)
from ape.pipeline.runner import ConstitutionalPipelineRunner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _QuickStage(PipelineStage):
    """Minimal stage that always succeeds immediately."""

    def __init__(self, name: str = "quick_stage") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def execute(
        self,
        context: BasePipelineContext,
        previous_results: List[StageResult],
    ) -> StageResult:
        return StageResult(
            stage_name=self.name,
            status=StageStatus.SUCCESS,
            output_data={"ok": True},
        )


class _SlowStage(PipelineStage):
    """Stage that sleeps for a given number of seconds to trigger time budget."""

    def __init__(self, sleep_seconds: float, name: str = "slow_stage") -> None:
        self._sleep = sleep_seconds
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def execute(
        self,
        context: BasePipelineContext,
        previous_results: List[StageResult],
    ) -> StageResult:
        time.sleep(self._sleep)
        return StageResult(
            stage_name=self.name,
            status=StageStatus.SUCCESS,
            output_data={"ok": True},
        )


def _ctx(resource_budget: dict | None = None) -> BasePipelineContext:
    return BasePipelineContext(
        run_id="test-run-001",
        resource_budget=resource_budget or {},
    )


# ---------------------------------------------------------------------------
# T1 — AC-1: ResourceBudget and ResourceUsage are importable
# ---------------------------------------------------------------------------

def test_resource_budget_dataclass_importable() -> None:
    """AC-1: ResourceBudget and ResourceUsage can be imported and instantiated."""
    b = ResourceBudget()
    u = ResourceUsage()
    assert b.max_tokens is None
    assert b.max_time_seconds is None
    assert b.max_cost_usd is None
    assert b.provider_quotas == {}
    assert b.max_retries == 3
    assert b.max_search_depth == 2
    assert u.tokens_used == 0
    assert u.time_elapsed_seconds == 0.0
    assert u.cost_usd == 0.0
    assert u.provider_calls == {}
    assert u.retry_count == 0
    assert u.search_depth_reached == 0


# ---------------------------------------------------------------------------
# T2–T5 — AC-2: is_exceeded() checks all 6 dimensions
# ---------------------------------------------------------------------------

def test_is_exceeded_token_limit() -> None:
    """AC-2a: tokens_used >= max_tokens triggers is_exceeded."""
    budget = ResourceBudget(max_tokens=100)
    usage = ResourceUsage(tokens_used=100)
    assert usage.is_exceeded(budget) is True

    usage_under = ResourceUsage(tokens_used=99)
    assert usage_under.is_exceeded(budget) is False


def test_is_exceeded_time_limit() -> None:
    """AC-2b: time_elapsed_seconds >= max_time_seconds triggers is_exceeded."""
    budget = ResourceBudget(max_time_seconds=30.0)
    usage = ResourceUsage(time_elapsed_seconds=30.0)
    assert usage.is_exceeded(budget) is True

    usage_under = ResourceUsage(time_elapsed_seconds=29.999)
    assert usage_under.is_exceeded(budget) is False


def test_is_exceeded_cost_limit() -> None:
    """AC-2c: cost_usd >= max_cost_usd triggers is_exceeded."""
    budget = ResourceBudget(max_cost_usd=1.00)
    usage = ResourceUsage(cost_usd=1.00)
    assert usage.is_exceeded(budget) is True

    usage_under = ResourceUsage(cost_usd=0.999)
    assert usage_under.is_exceeded(budget) is False


def test_is_exceeded_retry_limit() -> None:
    """AC-2d: retry_count > max_retries triggers is_exceeded (strict greater-than)."""
    budget = ResourceBudget(max_retries=3)
    usage_at_limit = ResourceUsage(retry_count=3)
    assert usage_at_limit.is_exceeded(budget) is False  # exactly at limit is OK

    usage_over = ResourceUsage(retry_count=4)
    assert usage_over.is_exceeded(budget) is True


# ---------------------------------------------------------------------------
# T6 — AC-3+4: Runner raises ResourceBudgetExceededError on time breach
# ---------------------------------------------------------------------------

def test_runner_raises_on_budget_exceeded() -> None:
    """AC-3+4: Runner pre-stage check raises ResourceBudgetExceededError on time excess.

    Uses max_time_seconds=0.0 so the budget is exceeded immediately before the
    first stage executes (time.monotonic() - pipeline_start > 0).
    """
    runner = ConstitutionalPipelineRunner([_QuickStage("first"), _QuickStage("second")])
    ctx = _ctx(resource_budget={"max_time_seconds": 0.0})  # triggers immediately

    with pytest.raises(ResourceBudgetExceededError) as exc_info:
        runner.run(ctx)

    assert "first" in str(exc_info.value)


# ---------------------------------------------------------------------------
# T7 — AC-5: budget_exhausted event written to evidence
# ---------------------------------------------------------------------------

def test_budget_exhausted_event_written_to_evidence(tmp_path: Path) -> None:
    """AC-5: _emit_budget_exhausted writes a BUDGET_EXHAUSTED event to governance evidence."""
    from ape.pipeline.runner import _emit_budget_exhausted  # noqa: PLC0415

    evidence_dir = tmp_path / ".governance" / "evidence"
    evidence_dir.mkdir(parents=True)
    ctx = BasePipelineContext(
        run_id="budget-test-run",
        resource_budget={},
        metadata={"project_root": str(tmp_path)},
    )
    budget = ResourceBudget(max_time_seconds=5.0)
    usage = ResourceUsage(time_elapsed_seconds=6.0)

    with patch("ape.utils.append_to_evidence") as mock_append:
        _emit_budget_exhausted(ctx, "test_stage", usage, budget)

    mock_append.assert_called_once()
    args = mock_append.call_args[0]
    assert args[2]["event"] == "BUDGET_EXHAUSTED"
    assert args[2]["run_id"] == "budget-test-run"
    assert args[2]["stage_attempted"] == "test_stage"
    assert args[2]["usage"]["time_elapsed_seconds"] == 6.0


# ---------------------------------------------------------------------------
# T8 — AC-6: ResourceUsage lineage appended on pipeline completion
# ---------------------------------------------------------------------------

def test_usage_lineage_appended_on_completion(tmp_path: Path) -> None:
    """AC-6: _emit_usage_lineage writes a PIPELINE_RESOURCE_USAGE event on success."""
    from ape.pipeline.runner import _emit_usage_lineage  # noqa: PLC0415

    ctx = BasePipelineContext(
        run_id="lineage-test-run",
        resource_budget={},
        metadata={"project_root": str(tmp_path)},
    )
    usage = ResourceUsage(time_elapsed_seconds=2.5, retry_count=1)

    with patch("ape.utils.append_to_evidence") as mock_append:
        _emit_usage_lineage(ctx, usage)

    mock_append.assert_called_once()
    args = mock_append.call_args[0]
    assert args[2]["event"] == "PIPELINE_RESOURCE_USAGE"
    assert args[2]["usage"]["time_elapsed_seconds"] == 2.5
    assert args[2]["usage"]["retry_count"] == 1


# ---------------------------------------------------------------------------
# T9 — AC-7: Default budget profiles are importable and correct
# ---------------------------------------------------------------------------

def test_default_budget_profiles_importable() -> None:
    """AC-7: DEFAULT_RESEARCH_BUDGET, DEFAULT_EXECUTION_BUDGET, STRICT_CI_BUDGET exist."""
    assert DEFAULT_RESEARCH_BUDGET.max_tokens == 50_000
    assert DEFAULT_RESEARCH_BUDGET.max_time_seconds == 300.0
    assert DEFAULT_RESEARCH_BUDGET.max_cost_usd == 1.00
    assert DEFAULT_RESEARCH_BUDGET.max_search_depth == 2

    assert DEFAULT_EXECUTION_BUDGET.max_tokens == 150_000
    assert DEFAULT_EXECUTION_BUDGET.max_time_seconds == 600.0
    assert DEFAULT_EXECUTION_BUDGET.max_cost_usd == 3.00
    assert DEFAULT_EXECUTION_BUDGET.max_retries == 3

    assert STRICT_CI_BUDGET.max_tokens == 20_000
    assert STRICT_CI_BUDGET.max_time_seconds == 120.0
    assert STRICT_CI_BUDGET.max_cost_usd == 0.25
    assert STRICT_CI_BUDGET.max_retries == 1


# ---------------------------------------------------------------------------
# T10 — Negative: no budget defined → pipeline runs without enforcement
# ---------------------------------------------------------------------------

def test_runner_budget_check_skipped_when_no_budget() -> None:
    """Negative T10: When resource_budget is empty, no enforcement occurs.

    The pipeline must complete normally even if stages are slow.
    """
    runner = ConstitutionalPipelineRunner([_QuickStage("s1"), _QuickStage("s2")])
    ctx = _ctx(resource_budget={})  # no budget keys → _extract_budget returns None

    results = runner.run(ctx)
    assert len(results) == 2
    assert all(r.status == StageStatus.SUCCESS for r in results)


# ---------------------------------------------------------------------------
# T11 — Negative: None dimensions not checked by is_exceeded
# ---------------------------------------------------------------------------

def test_is_exceeded_none_fields_not_checked() -> None:
    """Negative T11: Dimensions set to None on the budget are skipped by is_exceeded."""
    # max_tokens=None → even very high token usage should not trigger
    budget = ResourceBudget(max_tokens=None, max_time_seconds=None, max_cost_usd=None)
    usage = ResourceUsage(
        tokens_used=10_000_000,
        time_elapsed_seconds=99999.0,
        cost_usd=9999.0,
    )
    # Only retry and search_depth remain — with defaults (3, 2) and usage at 0
    assert usage.is_exceeded(budget) is False


# ---------------------------------------------------------------------------
# T12 — Phase 1 honesty: passive dimensions stay zero and do not enforce
# ---------------------------------------------------------------------------

def test_tokens_used_stays_zero_in_phase1() -> None:
    """T12: Passive dimensions (tokens_used, cost_usd, provider_calls, search_depth_reached)
    remain at zero throughout Phase 1 pipeline execution and do NOT trigger enforcement.

    This test documents the Phase 1 claim/evidence boundary explicitly:
    these dimensions are structurally present but not yet wired to telemetry sources.
    """
    runner = ConstitutionalPipelineRunner([_QuickStage("a"), _QuickStage("b")])
    # Set very low limits on the passive dimensions — they must NOT fire
    ctx = _ctx(resource_budget={
        "max_tokens": 1,       # passive: tokens_used will be 0 → no breach
        "max_cost_usd": 0.001, # passive: cost_usd will be 0.0 → no breach
        "max_time_seconds": 60.0,  # real: will not be reached in test
    })

    # Should NOT raise — passive dimensions never accumulate
    results = runner.run(ctx)
    assert len(results) == 2
    assert all(r.status == StageStatus.SUCCESS for r in results)


# ---------------------------------------------------------------------------
# T_profile — _extract_budget profile resolution
# ---------------------------------------------------------------------------

def test_extract_budget_profile_resolution() -> None:
    """_extract_budget resolves profile strings to canonical ResourceBudget instances."""
    from ape.pipeline.runner import _extract_budget  # noqa: PLC0415

    ctx_research = _ctx(resource_budget={"profile": "research"})
    assert _extract_budget(ctx_research) is DEFAULT_RESEARCH_BUDGET

    ctx_exec = _ctx(resource_budget={"profile": "execution"})
    assert _extract_budget(ctx_exec) is DEFAULT_EXECUTION_BUDGET

    ctx_ci = _ctx(resource_budget={"profile": "strict_ci"})
    assert _extract_budget(ctx_ci) is STRICT_CI_BUDGET

    ctx_empty = _ctx(resource_budget={})
    assert _extract_budget(ctx_empty) is None
