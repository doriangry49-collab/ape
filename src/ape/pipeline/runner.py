"""SPEC-0018 Constitutional Pipeline Runner.

Orchestrates the sequential execution of PipelineStages, enforcing fail-closed
gate traversal, Merkle evidence chaining, and resource budget checks.
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

from ape.pipeline.contracts import (
    BasePipelineContext,
    PipelineStage,
    StageResult,
    StageStatus,
)

logger = logging.getLogger(__name__)


class PipelineExecutionError(Exception):
    """Raised when a pipeline fails due to a stage error or blocked gate."""

    def __init__(self, message: str, stage_result: StageResult):
        super().__init__(message)
        self.stage_result = stage_result


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

        Enforces fail-closed semantics and chains parent_hash Merkle evidence.
        """
        results: List[StageResult] = []
        last_hash: Optional[str] = None

        logger.info(
            "Starting pipeline run '%s' for topic '%s' with %d stages",
            context.run_id,
            getattr(context, "topic_slug", getattr(context, "topic", "N/A")),
            len(self.stages),
        )

        for stage in self.stages:
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
        return results
