"""ExecutionPlanStage — Loads roadmap and existing execution state for execution pipelines.

Enforces fail-closed invariants:
- Fails if roadmap artifact does not exist for the specified topic_slug.
- Fails if roadmap contains zero executable tasks.

Stage Purity: Read-only stage. Does not mutate disk or create state files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional

from ape.intelligence.execution.models import ExecutionState, ExecutionTask
from ape.pipeline.contracts import (
    BasePipelineContext,
    ExecutionContext,
    PipelineStage,
    StageResult,
    StageStatus,
)
from ape.utils import get_current_artifact


def _infer_action(description: str) -> str:
    """Heuristic: infer action type from task description text."""
    desc = description.lower()
    if any(kw in desc for kw in ("modify", "update", "edit", "change", "refactor")):
        return "modify_file"
    if any(kw in desc for kw in ("delete", "remove")):
        return "delete_file"
    if any(kw in desc for kw in ("deploy", "publish", "release")):
        return "deploy"
    if any(kw in desc for kw in ("commit",)):
        return "git_commit"
    if any(kw in desc for kw in ("push",)):
        return "git_push"
    if any(kw in desc for kw in ("test", "pytest", "run tests")):
        return "run_tests"
    return "create_file"


class ExecutionPlanStage(PipelineStage):
    """Pipeline stage that reads roadmap and prepares the initial execution plan."""

    def __init__(self, project_root: Path) -> None:
        self._root = project_root

    @property
    def name(self) -> str:
        return "execution_plan"

    def execute(
        self,
        context: BasePipelineContext,
        previous_results: List[StageResult],
    ) -> StageResult:
        if not isinstance(context, ExecutionContext):
            # Fallback/support if context has topic_slug
            topic_slug = getattr(context, "topic_slug", "")
            topic = getattr(context, "topic", "")
        else:
            topic_slug = context.topic_slug
            topic = context.topic

        if not topic_slug or not topic_slug.strip():
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error="Invalid or empty topic_slug provided in context.",
            )

        # 1. Read existing state if present (read-only)
        state_file = self._root / ".build" / "execution" / topic_slug / "current.json"
        existing_state: Optional[ExecutionState] = None
        existing_state_dict: Optional[Dict[str, Any]] = None
        if state_file.exists():
            try:
                existing_state_dict = json.loads(state_file.read_text(encoding="utf-8"))
                existing_state = ExecutionState.from_dict(existing_state_dict)
            except Exception:
                existing_state = None

        # 2. Load roadmap
        roadmaps_dir = self._root / ".build" / "roadmaps"
        roadmap_file = get_current_artifact(roadmaps_dir, topic_slug)

        tasks: List[ExecutionTask] = []
        roadmap_id = "UNKNOWN"
        roadmap_raw: Optional[Dict[str, Any]] = None

        if roadmap_file and roadmap_file.exists():
            try:
                roadmap_raw = json.loads(roadmap_file.read_text(encoding="utf-8"))
                roadmap_id = roadmap_raw.get("roadmap_id", "UNKNOWN")
                for milestone in roadmap_raw.get("milestones", []):
                    for idx, t in enumerate(milestone.get("tasks", [])):
                        action = t.get("action") or _infer_action(t.get("description", ""))
                        task_id = t.get("task_id") or f"task_{idx + 1}"
                        tasks.append(
                            ExecutionTask(
                                task_id=task_id,
                                description=t.get("description", ""),
                                deliverables=t.get("deliverables", []),
                                action=action,
                            )
                        )
            except Exception as exc:
                return StageResult(
                    stage_name=self.name,
                    status=StageStatus.FAILED,
                    error=f"Failed to parse roadmap JSON for '{topic_slug}': {exc}",
                )
        elif existing_state and existing_state.tasks:
            # Resume mode from injected ExecutionState
            tasks = existing_state.tasks
            roadmap_id = existing_state.roadmap_id
        elif not (existing_state_dict or roadmap_file):
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error=f"Roadmap not found for topic_slug: '{topic_slug}'. Run `ape plan` first.",
            )

        # Invariant: Must contain at least one task unless existing state exists
        if not tasks and not existing_state_dict:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error=f"Roadmap for '{topic_slug}' contains zero executable tasks.",
            )

        task_ids = [t.task_id for t in tasks]

        execution_plan_summary = {
            "roadmap_id": roadmap_id,
            "task_count": len(tasks),
            "task_ids": task_ids,
            "resume_supported": existing_state is not None,
            "state_exists": existing_state is not None,
        }

        output_data = {
            "execution_plan": execution_plan_summary,
            "tasks": [t.to_dict() for t in tasks],
            "roadmap_id": roadmap_id,
            "roadmap_raw": roadmap_raw,
            "existing_state": existing_state.to_dict() if existing_state else None,
        }

        evidence = {
            "roadmap_id": roadmap_id,
            "task_count": len(tasks),
            "topic_slug": topic_slug,
        }

        return StageResult(
            stage_name=self.name,
            status=StageStatus.SUCCESS,
            output_data=output_data,
            evidence=evidence,
        )
