"""SPEC-0018 Constitutional Pipeline Runner.

Orchestrates the sequential execution of PipelineStages, enforcing fail-closed
gate traversal, Merkle evidence chaining, and resource budget checks.

SPEC-0019 Integration (Phase 1):
  - INV-1: Pre-stage budget check before each PipelineStage execution.
  - INV-2: ResourceBudgetExceededError raised + budget_exhausted evidence emitted.
  - INV-3: retry_count consumed post-TaskExecutionStage (weak enforcement).
  - INV-4: ResourceUsage lineage appended to pipeline evidence on completion.

Phase 1 enforcement honesty — see resource_budget.py for the full passive/active matrix.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ape.pipeline.contracts import (
    BasePipelineContext,
    PipelineStage,
    StageResult,
    StageStatus,
)
from ape.pipeline.resource_budget import (
    DEFAULT_EXECUTION_BUDGET,
    DEFAULT_RESEARCH_BUDGET,
    STRICT_CI_BUDGET,
    ResourceBudget,
    ResourceBudgetExceededError,
    ResourceUsage,
)

logger = logging.getLogger(__name__)


class PipelineExecutionError(Exception):
    """Raised when a pipeline fails due to a stage error or blocked gate."""

    def __init__(self, message: str, stage_result: StageResult):
        super().__init__(message)
        self.stage_result = stage_result


# ---------------------------------------------------------------------------
# Internal helpers (module-private)
# ---------------------------------------------------------------------------

def _extract_budget(context: BasePipelineContext) -> Optional[ResourceBudget]:
    """Derives a ResourceBudget from context.resource_budget (SPEC-0019 §4).

    Supports three forms:
      1. {"profile": "research"|"execution"|"strict_ci"} → canonical profile
      2. {"max_tokens": N, "max_time_seconds": T, ...}   → ad-hoc ResourceBudget
      3. {}  or no recognized keys                        → None (no enforcement)

    The field type in contracts.py (Dict[str, Any]) is intentionally preserved
    to maintain full backward compatibility across all call sites.
    """
    raw: Dict[str, Any] = context.resource_budget
    if not raw:
        return None

    profile = raw.get("profile")
    if profile == "research":
        return DEFAULT_RESEARCH_BUDGET
    if profile == "execution":
        return DEFAULT_EXECUTION_BUDGET
    if profile == "strict_ci":
        return STRICT_CI_BUDGET

    known_keys = {"max_tokens", "max_time_seconds", "max_cost_usd",
                  "provider_quotas", "max_retries", "max_search_depth"}
    if not any(k in raw for k in known_keys):
        return None

    return ResourceBudget(
        max_tokens=raw.get("max_tokens"),
        max_time_seconds=raw.get("max_time_seconds"),
        max_cost_usd=raw.get("max_cost_usd"),
        provider_quotas=raw.get("provider_quotas", {}),
        max_retries=raw.get("max_retries", 3),
        max_search_depth=raw.get("max_search_depth", 2),
    )


def _emit_budget_exhausted(
    context: BasePipelineContext,
    stage_name: str,
    usage: ResourceUsage,
    budget: ResourceBudget,
) -> None:
    """Appends a budget_exhausted governance evidence event (SPEC-0019 §3 INV-2).

    Falls back to logging if project_root is unavailable (e.g. research pipelines).
    """
    payload: Dict[str, Any] = {
        "event": "BUDGET_EXHAUSTED",
        "run_id": context.run_id,
        "stage_attempted": stage_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "usage": usage.to_dict(),
        "budget": {
            "max_tokens": budget.max_tokens,
            "max_time_seconds": budget.max_time_seconds,
            "max_cost_usd": budget.max_cost_usd,
            "max_retries": budget.max_retries,
            "max_search_depth": budget.max_search_depth,
        },
    }
    project_root_raw = context.metadata.get("project_root") if context.metadata else None
    if project_root_raw:
        try:
            from ape.utils import append_to_evidence
            evidence_dir = Path(str(project_root_raw)) / ".governance" / "evidence"
            append_to_evidence(evidence_dir, "pipeline", payload)
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("budget_exhausted evidence append failed: %s", exc)
    logger.error("BUDGET_EXHAUSTED (no project_root for evidence write): %s", payload)


def _emit_usage_lineage(
    context: BasePipelineContext,
    usage: ResourceUsage,
) -> None:
    """Appends ResourceUsage lineage to pipeline evidence on completion (SPEC-0019 §3 INV-4)."""
    payload: Dict[str, Any] = {
        "event": "PIPELINE_RESOURCE_USAGE",
        "run_id": context.run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "usage": usage.to_dict(),
    }
    project_root_raw = context.metadata.get("project_root") if context.metadata else None
    if project_root_raw:
        try:
            from ape.utils import append_to_evidence
            evidence_dir = Path(str(project_root_raw)) / ".governance" / "evidence"
            append_to_evidence(evidence_dir, "pipeline", payload)
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("pipeline resource usage lineage append failed: %s", exc)
    logger.info("PIPELINE_RESOURCE_USAGE (no project_root): %s", payload)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

class ConstitutionalPipelineRunner:
    """Orchestrates pipeline stages with strict evidence logging, Merkle lineage, and fail-closed security."""

    def __init__(self, stages: Optional[List[PipelineStage]] = None):
        self.stages: List[PipelineStage] = stages or []

    def add_stage(self, stage: PipelineStage) -> ConstitutionalPipelineRunner:
        """Appends a stage to the pipeline sequence."""
        self.stages.append(stage)
        return self

    def run(self, context: BasePipelineContext) -> List[StageResult]:
        """Executes registered stages in sequence.

        Enforces fail-closed semantics, chains parent_hash Merkle evidence,
        and applies SPEC-0019 resource budget checks (INV-1/INV-2/INV-3/INV-4).

        The public signature is unchanged: callers pass only `context`.
        Budget is derived internally from context.resource_budget (Dict[str, Any]).
        """
        results: List[StageResult] = []
        last_hash: Optional[str] = None

        # SPEC-0019 INV-1/INV-2: budget and usage tracker (runner-internal)
        budget: Optional[ResourceBudget] = _extract_budget(context)
        usage = ResourceUsage()
        pipeline_start = time.monotonic()   # wall-clock anchor for time_elapsed_seconds

        logger.info(
            "Starting pipeline run '%s' for topic '%s' with %d stages",
            context.run_id,
            getattr(context, "topic_slug", getattr(context, "topic", "N/A")),
            len(self.stages),
        )

        for stage in self.stages:
            # ── SPEC-0019 INV-1: Pre-stage budget check ──────────────────────
            # time_elapsed_seconds is the only REAL dimension in Phase 1.
            # Other dimensions (tokens, cost, provider_calls, search_depth)
            # remain at their zero/empty defaults and will not trigger enforcement
            # until a future ORION wires their telemetry sources.
            usage.time_elapsed_seconds = time.monotonic() - pipeline_start
            if budget is not None and usage.is_exceeded(budget):
                _emit_budget_exhausted(context, stage.name, usage, budget)
                raise ResourceBudgetExceededError(
                    f"Resource budget exceeded before stage '{stage.name}'. "
                    f"Usage: {usage.to_dict()}"
                )
            # ─────────────────────────────────────────────────────────────────

            logger.debug("Executing pipeline stage: %s", stage.name)
            start_time = time.perf_counter()
            started_timestamp = time.time()

            try:
                result = stage.execute(context, results)
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                logger.error("Unhandled exception in stage '%s': %s", stage.name, exc)
                result = StageResult(
                    stage_name=stage.name,
                    status=StageStatus.FAILED,
                    error=str(exc),
                    duration_ms=elapsed_ms,
                    started_at=started_timestamp,
                )

            # Ensure timestamps, duration, and Merkle chaining are set
            finished_timestamp = time.time()
            result.started_at = started_timestamp
            result.finished_at = finished_timestamp
            if result.duration_ms == 0.0:
                result.duration_ms = (time.perf_counter() - start_time) * 1000.0

            result.parent_hash = last_hash
            stage_hash = result.compute_stage_hash()
            result.evidence["stage_hash"] = stage_hash
            result.evidence["parent_hash"] = last_hash
            result.evidence["lineage_id"] = context.run_id

            last_hash = stage_hash
            results.append(result)

            # SPEC-0019 INV-3 (weak): update retry_count from TaskExecutionStage output
            if stage.name == "task_execution" and result.status == StageStatus.SUCCESS:
                retried = result.output_data.get("execution_summary", {}).get("retried", [])
                usage.retry_count += len(retried)

            # Fail-closed invariant check
            if result.status in (StageStatus.FAILED, StageStatus.BLOCKED):
                logger.error(
                    "Pipeline halted at stage '%s' with status %s: %s",
                    stage.name,
                    result.status.value,
                    result.error,
                )
                raise PipelineExecutionError(
                    f"Pipeline execution halted at stage '{stage.name}' with status '{result.status.value}': {result.error}",
                    stage_result=result,
                )

        logger.info("Pipeline run '%s' completed successfully", context.run_id)

        # SPEC-0019 INV-4: append ResourceUsage lineage on pipeline completion
        usage.time_elapsed_seconds = time.monotonic() - pipeline_start
        _emit_usage_lineage(context, usage)

        return results
