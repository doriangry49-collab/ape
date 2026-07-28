"""
Execution Engine — orchestrates the full execution lifecycle.

Canonical state:  .build/execution/<slug>/current.json  (mutable)
Immutable history: .governance/evidence/execution.jsonl  (append-only)

No LLM provider dependency. No direct shell execution in MVP.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ape.intelligence.execution.executor import SimulationTaskExecutor, TaskExecutor
from ape.intelligence.execution.models import (
    ExecutionState,
    ExecutionStatus,
    ExecutionTask,
    TaskStatus,
)
from ape.intelligence.execution.policy import ExecutionPolicy
from ape.intelligence.execution.state import TaskStateMachine
from ape.intelligence.execution.verifier import DeliverableVerifier
from ape.utils import append_to_evidence, get_current_artifact


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


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


class ExecutionEngine:
    """
    Orchestrates task execution from a Roadmap artifact.

    Parameters
    ----------
    project_root       : Path to the APE workspace root.
    dry_run            : If True (default), use SimulationTaskExecutor.
    interrupt_after_tasks : For testing: simulate KeyboardInterrupt after N tasks.
    auto_deny_approvals   : For testing: auto-deny all approval requests.
    executor           : Optional custom TaskExecutor (for future extensibility).
    """

    def __init__(
        self,
        project_root: Path,
        dry_run: bool = True,
        interrupt_after_tasks: Optional[int] = None,
        auto_deny_approvals: bool = False,
        executor: Optional[TaskExecutor] = None,
    ) -> None:
        self._root = project_root
        self._dry_run = dry_run
        self._interrupt_after = interrupt_after_tasks
        self._auto_deny = auto_deny_approvals
        self._policy = ExecutionPolicy()
        self._executor = executor or SimulationTaskExecutor()
        self._verifier = DeliverableVerifier(project_root, dry_run=dry_run)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(self, topic: str, topic_slug: str) -> dict:
        """
        Main entry point for `ape execute`.
        Loads or creates ExecutionState from Roadmap, then runs the task queue.
        """
        # 1. Load roadmap
        roadmap_file = get_current_artifact(
            self._root / ".build" / "roadmaps", topic_slug
        )
        if not roadmap_file:
            raise FileNotFoundError(
                f"Roadmap not found for: {topic_slug}. Run `ape plan` first."
            )

        roadmap = json.loads(roadmap_file.read_text(encoding="utf-8"))

        # 2. Load or create state
        state = self._load_or_create_state(topic, topic_slug, roadmap)

        # 3. Persist initial/current state
        self._save_state(topic_slug, state)

        # 4. Run task queue
        return self._run_queue(topic_slug, state)

    def resume_or_start(self, topic_slug: str) -> dict:
        """
        Resume from an existing ExecutionState.
        Used in tests to inject a pre-built state.
        Returns dict with keys: executed, retried, skipped, paused.
        """
        state = self._load_state(topic_slug)
        if state is None:
            return {"executed": [], "retried": [], "skipped": [], "paused": []}
        return self._run_queue(topic_slug, state)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_or_create_state(
        self, topic: str, topic_slug: str, roadmap: dict
    ) -> ExecutionState:
        existing = self._load_state(topic_slug)
        if existing is not None:
            return existing

        # Build fresh task list from roadmap
        tasks: list[ExecutionTask] = []
        for milestone in roadmap.get("milestones", []):
            for t in milestone.get("tasks", []):
                action = t.get("action") or _infer_action(t.get("description", ""))
                tasks.append(ExecutionTask(
                    task_id=t["task_id"],
                    description=t.get("description", ""),
                    deliverables=t.get("deliverables", []),
                    action=action,
                ))

        return ExecutionState(
            execution_id=f"exec_{uuid.uuid4().hex[:8]}",
            roadmap_id=roadmap.get("roadmap_id", "UNKNOWN"),
            topic=topic,
            tasks=tasks,
        )

    def _load_state(self, topic_slug: str) -> Optional[ExecutionState]:
        state_file = (
            self._root / ".build" / "execution" / topic_slug / "current.json"
        )
        if not state_file.exists():
            return None
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            return ExecutionState.from_dict(data)
        except (KeyError, ValueError):
            # Malformed / foreign state file — treat as no prior state.
            return None

    def _save_state(self, topic_slug: str, state: ExecutionState) -> None:
        if self._dry_run:
            # dry-run: never overwrite existing real state
            existing_path = (
                self._root / ".build" / "execution" / topic_slug / "current.json"
            )
            if existing_path.exists():
                existing = json.loads(existing_path.read_text(encoding="utf-8"))
                if existing.get("sentinel"):  # real sentinel state — don't touch
                    return
        state.updated_at = _utcnow()
        state_dir = self._root / ".build" / "execution" / topic_slug
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "current.json").write_text(
            json.dumps(state.to_dict(), indent=2), encoding="utf-8"
        )

    def _emit(self, topic_slug: str, event: str, task_id: str, **extra: object) -> None:
        payload = {
            "event": event,
            "task_id": task_id,
            "topic_slug": topic_slug,
            "timestamp": _utcnow(),
            **extra,
        }
        append_to_evidence(
            self._root / ".governance" / "evidence", "execution", payload
        )

    def _run_queue(self, topic_slug: str, state: ExecutionState) -> dict:
        summary: dict[str, list[str]] = {
            "executed": [], "retried": [], "skipped": [], "paused": []
        }
        tasks_run = 0

        try:
            for task in state.tasks:
                sm = TaskStateMachine(task)

                # Resume semantics
                if task.status == TaskStatus.COMPLETED:
                    summary["skipped"].append(task.task_id)
                    continue

                if task.status == TaskStatus.FAILED:
                    sm.retry()
                    self._emit(topic_slug, "STARTED", task.task_id, retry=True)
                    summary["retried"].append(task.task_id)
                elif task.status in (TaskStatus.PAUSED, TaskStatus.IN_PROGRESS):
                    sm.resume()
                    self._emit(topic_slug, "STARTED", task.task_id, resumed=True)
                    summary["executed"].append(task.task_id)
                else:
                    # PENDING or REQUIRES_APPROVAL
                    safety = self._policy.classify(task.action)

                    if safety == "FORBIDDEN":
                        sm.fail(error="Action is FORBIDDEN by ExecutionPolicy.")
                        self._emit(topic_slug, "FAILED", task.task_id,
                                   reason="FORBIDDEN")
                        self._save_state(topic_slug, state)
                        continue

                    if safety == "REQUIRES_APPROVAL":
                        sm.request_approval()
                        self._save_state(topic_slug, state)
                        self._emit(topic_slug, "REQUIRES_APPROVAL", task.task_id)

                        if self._auto_deny:
                            sm.deny()
                            self._save_state(topic_slug, state)
                            continue

                        # In real CLI: would prompt user. In test/dry-run: auto-deny.
                        answer = self._prompt_approval(task)
                        if not answer:
                            sm.deny()
                            self._save_state(topic_slug, state)
                            continue
                        sm.approve()
                        self._emit(topic_slug, "APPROVED", task.task_id)

                    else:
                        # SAFE
                        sm.start()
                        self._emit(topic_slug, "STARTED", task.task_id)
                        summary["executed"].append(task.task_id)

                # Execute (simulation in MVP)
                self._executor.execute(task.description, task.deliverables)

                # Verify deliverables
                ok, missing = self._verifier.verify(task.deliverables)
                if ok:
                    sm.complete()
                    self._emit(topic_slug, "COMPLETED", task.task_id)
                    self._emit(topic_slug, "VERIFIED", task.task_id,
                               deliverables=task.deliverables)
                else:
                    sm.fail(error=f"Missing deliverables: {missing}")
                    self._emit(topic_slug, "FAILED", task.task_id,
                               missing=missing)

                self._save_state(topic_slug, state)
                tasks_run += 1

                # Test hook: simulate Ctrl+C after N tasks
                if self._interrupt_after and tasks_run >= self._interrupt_after:
                    raise KeyboardInterrupt

        except KeyboardInterrupt:
            # Centralised PAUSED transition
            for task in state.tasks:
                if task.status == TaskStatus.IN_PROGRESS:
                    TaskStateMachine(task).pause()
                    summary["paused"].append(task.task_id)

            state.status = ExecutionStatus.PAUSED
            self._save_state(topic_slug, state)
            self._emit(topic_slug, "PAUSED", "engine", reason="KeyboardInterrupt")

        else:
            all_done = all(t.status == TaskStatus.COMPLETED for t in state.tasks)
            state.status = (
                ExecutionStatus.COMPLETED if all_done else ExecutionStatus.IN_PROGRESS
            )
            self._save_state(topic_slug, state)

        return summary

    def _prompt_approval(self, task: ExecutionTask) -> bool:
        """In MVP / dry-run: auto-deny. In real CLI: prompt user."""
        if self._dry_run:
            return False
        try:
            answer = input(
                f"\nTask: {task.description}\n"
                f"Action: {task.action}\n"
                f"Safety: REQUIRES_APPROVAL\n"
                f"Proceed? [y/N] "
            ).strip().lower()
            return answer == "y"
        except (EOFError, KeyboardInterrupt):
            return False
