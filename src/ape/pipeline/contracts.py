"""SPEC-0018 Constitutional Pipeline Core Contracts.

This module defines the immutable context, stage results, stage status,
lineage, and pipeline stage interfaces that form the constitutional backbone of APE.
"""

from __future__ import annotations

import abc
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class StageStatus(str, Enum):
    """Execution status of a pipeline stage."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class BasePipelineContext:
    """Minimal immutable base context passed through pipeline execution sequences."""

    run_id: str
    resource_budget: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResearchContext(BasePipelineContext):
    """Domain context specific to Research Pipelines."""

    topic_slug: str = ""

    def with_updates(
        self,
        resource_budget: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        topic_slug: Optional[str] = None,
    ) -> ResearchContext:
        """Returns a new ResearchContext with controlled, explicit updates preserving immutability."""
        new_budget = dict(self.resource_budget)
        if resource_budget:
            new_budget.update(resource_budget)

        new_meta = dict(self.metadata)
        if metadata:
            new_meta.update(metadata)

        return ResearchContext(
            run_id=self.run_id,
            resource_budget=new_budget,
            metadata=new_meta,
            topic_slug=topic_slug if topic_slug is not None else self.topic_slug,
        )


# Backward compatibility alias / default context type for Research Pipelines
PipelineContext = ResearchContext


@dataclass(frozen=True)
class ExecutionContext(BasePipelineContext):
    """Domain context specific to Execution Pipelines."""

    topic_slug: str = ""
    topic: str = ""
    dry_run: bool = True
    auto_deny_approvals: bool = False
    interrupt_after_tasks: Optional[int] = None
    execution_mode: str = "SIMULATION"        # "SIMULATION" | "REAL_SANDBOX"
    execution_backend: str = "SIMULATION_STUB" # "SIMULATION_STUB" | "DOCKER_SANDBOX"

    def with_updates(
        self,
        resource_budget: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        topic_slug: Optional[str] = None,
        topic: Optional[str] = None,
        dry_run: Optional[bool] = None,
        auto_deny_approvals: Optional[bool] = None,
        interrupt_after_tasks: Optional[int] = None,
        execution_mode: Optional[str] = None,
        execution_backend: Optional[str] = None,
    ) -> ExecutionContext:
        """Returns a new ExecutionContext with controlled, explicit updates preserving immutability."""
        new_budget = dict(self.resource_budget)
        if resource_budget:
            new_budget.update(resource_budget)

        new_meta = dict(self.metadata)
        if metadata:
            new_meta.update(metadata)

        eff_dry_run = dry_run if dry_run is not None else self.dry_run
        eff_mode = execution_mode if execution_mode is not None else ("SIMULATION" if eff_dry_run else "REAL_SANDBOX")
        eff_backend = execution_backend if execution_backend is not None else ("SIMULATION_STUB" if eff_dry_run else "DOCKER_SANDBOX")

        return ExecutionContext(
            run_id=self.run_id,
            resource_budget=new_budget,
            metadata=new_meta,
            topic_slug=topic_slug if topic_slug is not None else self.topic_slug,
            topic=topic if topic is not None else self.topic,
            dry_run=eff_dry_run,
            auto_deny_approvals=auto_deny_approvals if auto_deny_approvals is not None else self.auto_deny_approvals,
            interrupt_after_tasks=interrupt_after_tasks if interrupt_after_tasks is not None else self.interrupt_after_tasks,
            execution_mode=eff_mode,
            execution_backend=eff_backend,
        )


@dataclass
class StageResult:
    """Result, Merkle lineage, and evidence produced by a single pipeline stage execution."""

    stage_name: str
    status: StageStatus
    output_data: Dict[str, Any] = field(default_factory=dict)
    evidence: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: float = 0.0
    parent_hash: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None

    def compute_stage_hash(self) -> str:
        """Computes a deterministic SHA-256 evidence Merkle hash for this stage result."""
        payload = {
            "stage_name": self.stage_name,
            "status": self.status.value,
            "output_data": self.output_data,
            "evidence": self.evidence,
            "error": self.error,
            "parent_hash": self.parent_hash,
        }
        raw_bytes = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(raw_bytes).hexdigest()


class PipelineStage(abc.ABC):
    """Abstract base class for all constitutional pipeline stages."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique identifier of the stage."""
        pass

    @abc.abstractmethod
    def execute(
        self,
        context: BasePipelineContext,
        previous_results: List[StageResult],
    ) -> StageResult:
        """Executes stage logic, enforcing constitutional invariants and producing evidence."""
        pass
