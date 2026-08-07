"""CapabilityCheckStage — Assesses execution capabilities required by tasks.

Stage Invariants:
- Evaluates required vs resolved capabilities for the requested execution.
- Produces an Execution Environment Snapshot for auditing and downstream stages.
- Returns BLOCKED with structured blocked_reason if dry_run=False and required capabilities are missing.

Decoupled from specific backends via Capability Assessment Engine / Provider pattern.
"""

from __future__ import annotations

import platform
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ape.pipeline.contracts import (
    BasePipelineContext,
    ExecutionContext,
    PipelineStage,
    StageResult,
    StageStatus,
)


class CapabilityProvider:
    """Interface for collecting capability snapshots."""

    def collect(self, tasks: List[Dict[str, Any]], dry_run: bool = True) -> Dict[str, Any]:
        raise NotImplementedError


class LocalCapabilityProvider(CapabilityProvider):
    """Default local system capability provider."""

    def __init__(self, project_root: Path) -> None:
        self._root = project_root

    def collect(self, tasks: List[Dict[str, Any]], dry_run: bool = True) -> Dict[str, Any]:
        required: Set[str] = {"filesystem", "python"}

        for task in tasks:
            action = task.get("action", "")
            if action in ("deploy", "run_in_container", "docker_build"):
                required.add("docker")

        resolved: Set[str] = {"filesystem", "python"}
        if shutil.which("docker") is not None:
            resolved.add("docker")

        missing = required - resolved

        if dry_run:
            backend = "simulation"
            mode = "dry_run"
        elif "docker" in resolved:
            backend = "docker"
            mode = "live"
        else:
            backend = "local_sandbox"
            mode = "live"

        capabilities_map = {cap: (cap in resolved) for cap in required}

        environment_snapshot = {
            "backend": backend,
            "mode": mode,
            "capabilities": capabilities_map,
            "platform": {
                "os": platform.system().lower(),
                "sandbox": "docker" if "docker" in resolved else "local",
            },
        }

        return {
            "required_capabilities": sorted(list(required)),
            "resolved_capabilities": sorted(list(resolved)),
            "missing_capabilities": sorted(list(missing)),
            "execution_backend": backend,
            "execution_mode": mode,
            "environment_snapshot": environment_snapshot,
        }


class CapabilityCheckStage(PipelineStage):
    """Pipeline stage that checks capability readiness before task execution."""

    def __init__(
        self,
        project_root: Path,
        provider: Optional[CapabilityProvider] = None,
    ) -> None:
        self._root = project_root
        self._provider = provider or LocalCapabilityProvider(project_root)

    @property
    def name(self) -> str:
        return "capability_check"

    def execute(
        self,
        context: BasePipelineContext,
        previous_results: List[StageResult],
    ) -> StageResult:
        if not isinstance(context, ExecutionContext):
            dry_run = getattr(context, "dry_run", True)
        else:
            dry_run = context.dry_run

        tasks: List[Dict[str, Any]] = []
        for prev in previous_results:
            if prev.stage_name == "execution_plan" and "tasks" in prev.output_data:
                tasks = prev.output_data["tasks"]
                break

        snapshot_data = self._provider.collect(tasks=tasks, dry_run=dry_run)

        missing = snapshot_data["missing_capabilities"]
        backend = snapshot_data["execution_backend"]
        mode = snapshot_data["execution_mode"]
        snapshot = snapshot_data["environment_snapshot"]

        # Fast-Fail BLOCKED Check (Non-dry-run with missing capabilities)
        if not dry_run and missing:
            error_msg = (
                f"Execution BLOCKED: Required capability missing for live execution: {missing}. "
                "Please satisfy environment requirements or switch to dry_run mode."
            )
            blocked_reason = {
                "code": "MISSING_CAPABILITY",
                "message": f"Required capability missing: {missing}",
                "retryable": True,
            }

            return StageResult(
                stage_name=self.name,
                status=StageStatus.BLOCKED,
                error=error_msg,
                output_data={
                    "required_capabilities": snapshot_data["required_capabilities"],
                    "resolved_capabilities": snapshot_data["resolved_capabilities"],
                    "missing_capabilities": missing,
                    "execution_backend": backend,
                    "execution_mode": mode,
                    "environment_snapshot": snapshot,
                    "capabilities_satisfied": False,
                },
                evidence={
                    "blocked_reason": blocked_reason,
                    "failure_reason": "MISSING_REQUIRED_CAPABILITIES",
                    "missing_capabilities": missing,
                    "execution_backend": backend,
                    "execution_mode": mode,
                },
            )

        output_data = {
            "required_capabilities": snapshot_data["required_capabilities"],
            "resolved_capabilities": snapshot_data["resolved_capabilities"],
            "missing_capabilities": missing,
            "execution_backend": backend,
            "execution_mode": mode,
            "environment_snapshot": snapshot,
            "capabilities_satisfied": True,
        }

        evidence = {
            "execution_backend": backend,
            "execution_mode": mode,
            "missing_capabilities": missing,
            "resolved_capabilities": snapshot_data["resolved_capabilities"],
        }

        return StageResult(
            stage_name=self.name,
            status=StageStatus.SUCCESS,
            output_data=output_data,
            evidence=evidence,
        )
