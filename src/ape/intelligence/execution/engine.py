"""
Execution Engine — orchestrates the full execution lifecycle.

Canonical state:  .build/execution/<slug>/current.json  (mutable)
Immutable history: .governance/evidence/execution-YYYY-MM.jsonl  (append-only)

No LLM provider dependency. No direct shell execution in MVP.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ape.intelligence.execution.exceptions import (
    LineageMismatchError,
    PolicyExecutionBlockedError,
)
from ape.intelligence.execution.executor import (
    DockerSandboxExecutor,
    SimulationTaskExecutor,
    TaskExecutor,
)
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
        agent: Optional[Any] = None,
    ) -> None:
        self._root = project_root
        self._dry_run = dry_run
        self._interrupt_after = interrupt_after_tasks
        self._auto_deny = auto_deny_approvals
        self._policy = ExecutionPolicy()
        if executor:
            self._executor = executor
        elif dry_run:
            self._executor = SimulationTaskExecutor()
        else:
            self._executor = DockerSandboxExecutor()
        self._verifier = DeliverableVerifier(project_root, dry_run=dry_run)

        # RFC-016: Wire ApeCoderAgent if provided or if ConfigService has API Key configured
        self._agent = agent
        self.agent_init_error: Optional[str] = None
        if not self._agent:
            try:
                from ape.intelligence.execution.agent import ApeCoderAgent
                from ape.intelligence.roadmap.llm import OpenAICompatibleProvider
                from ape.project import Project
                from ape.services.config_service import ConfigService

                config_service = ConfigService(Project.load(project_root))
                api_key = config_service.planner_api_key
                if api_key:
                    try:
                        provider = OpenAICompatibleProvider(
                            api_key=api_key,
                            model=config_service.planner_model,
                            base_url=config_service.planner_base_url or "https://api.openai.com/v1"
                        )
                        self._agent = ApeCoderAgent(model=provider)
                    except Exception as exc:
                        self._agent = None
                        err_msg = str(exc)
                        if api_key in err_msg:
                            err_msg = err_msg.replace(api_key, "[REDACTED_API_KEY]")
                        self.agent_init_error = f"Agent provider wiring failed ({type(exc).__name__}): {err_msg}"
                        print(f"Warning: {self.agent_init_error}")
            except Exception as exc:
                self._agent = None
                self.agent_init_error = f"Agent configuration failed ({type(exc).__name__}): {str(exc)}"


    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(self, topic: str, topic_slug: str) -> dict:
        """
        Main entry point for `ape execute`.

        RFC-014: Decision gate is verified BEFORE any task is loaded or run.
        This is a second safety layer: even if `ape plan` was bypassed, a
        WATCH/IGNORE/BLOCKED decision cannot reach execution.
        """
        # 0. RFC-014: Verify PolicyDecision — raises on WATCH/IGNORE/BLOCKED
        decision_data = self._verify_decision_gate(topic_slug)

        # 1. Load roadmap
        roadmap_file = get_current_artifact(
            self._root / ".build" / "roadmaps", topic_slug
        )
        if not roadmap_file:
            raise FileNotFoundError(
                f"Roadmap not found for: {topic_slug}. Run `ape plan` first."
            )

        roadmap = json.loads(roadmap_file.read_text(encoding="utf-8"))

        # 2. Load or create state (passes decision_data for lineage)
        state = self._load_or_create_state(topic, topic_slug, roadmap, decision_data)

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
        # RFC-014 Fix: Never allow execution without verifying policy gate
        decision_data = self._verify_decision_gate(topic_slug)

        state = self._load_state(topic_slug)
        if state is None:
            return {"executed": [], "retried": [], "skipped": [], "paused": []}
            
        # Enforce lineage match on resume
        if decision_data and state.decision_id != decision_data.get("decision_id"):
            raise LineageMismatchError(
                f"Lineage mismatch on resume: ExecutionState decision_id '{state.decision_id}' "
                f"does not match current artifact decision_id '{decision_data.get('decision_id')}'. "
                "Cannot resume."
            )

        return self._run_queue(topic_slug, state)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _verify_decision_gate(self, topic_slug: str) -> dict:
        """
        RFC-014 Policy Gate: reads the decision artifact and blocks execution
        for WATCH, IGNORE, or BLOCKED decisions.

        Returns the parsed decision_data dict for downstream lineage use.
        Raises:
            FileNotFoundError: if no decision artifact exists.
            PolicyExecutionBlockedError: if decision is not BUILD or VALIDATE.
        """
        decision_file = get_current_artifact(
            self._root / ".build" / "decisions", topic_slug
        )
        if not decision_file:
            raise FileNotFoundError(
                f"No decision artifact found for: {topic_slug}. "
                "Run `ape decide` first."
            )
        decision_data = json.loads(decision_file.read_text(encoding="utf-8"))
        decision_val = str(decision_data.get("decision", "")).upper()
        if decision_val in ("WATCH", "IGNORE", "BLOCKED"):
            raise PolicyExecutionBlockedError(
                f"Execution blocked: PolicyDecision is '{decision_val}'. "
                "Only BUILD or VALIDATE decisions may be executed. "
                "(RFC-014 / SPEC-0014 §3)"
            )
        return decision_data

    def _load_or_create_state(
        self,
        topic: str,
        topic_slug: str,
        roadmap: dict,
        decision_data: Optional[dict] = None,
    ) -> ExecutionState:
        existing = self._load_state(topic_slug)
        if existing is not None:
            if decision_data and existing.decision_id != decision_data.get("decision_id"):
                raise LineageMismatchError(
                    f"Lineage mismatch on resume: ExecutionState decision_id '{existing.decision_id}' "
                    f"does not match current artifact decision_id '{decision_data.get('decision_id')}'. "
                    "Cannot resume."
                )
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

        # RFC-014: Propagate audit lineage from decision artifact into ExecutionState.
        dd = decision_data or {}
        return ExecutionState(
            execution_id=f"exec_{uuid.uuid4().hex[:8]}",
            roadmap_id=roadmap.get("roadmap_id", "UNKNOWN"),
            decision_id=dd.get("decision_id", roadmap.get("decision_id", "UNKNOWN")),
            policy_decision=str(dd.get("decision", roadmap.get("policy_decision", "UNKNOWN"))).upper(),
            evidence_hash=dd.get("evidence_hash", ""),
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

    def _emit(
        self,
        topic_slug: str,
        event: str,
        task_id: str,
        state: Optional["ExecutionState"] = None,
        **extra: object,
    ) -> None:
        # RFC-014: Include decision lineage in every execution event.
        lineage: dict = {}
        if state is not None:
            lineage = {
                "decision_id": state.decision_id,
                "policy_decision": state.policy_decision,
                "evidence_hash": state.evidence_hash,
            }
        payload = {
            "event": event,
            "task_id": task_id,
            "topic_slug": topic_slug,
            "timestamp": _utcnow(),
            **lineage,
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
                    self._emit(topic_slug, "STARTED", task.task_id, state=state, retry=True)
                    summary["retried"].append(task.task_id)
                elif task.status in (TaskStatus.PAUSED, TaskStatus.IN_PROGRESS):
                    sm.resume()
                    self._emit(topic_slug, "STARTED", task.task_id, state=state, resumed=True)
                    summary["executed"].append(task.task_id)
                else:
                    # PENDING or REQUIRES_APPROVAL
                    safety = self._policy.classify(task.action)

                    # Check path containment for deliverable targets
                    if task.action in ("create_file", "modify_file"):
                        from ape.intelligence.execution.policy import validate_path_containment
                        path_blocked = False
                        for d in task.deliverables:
                            if d and isinstance(d, str):
                                ok, err = validate_path_containment(self._root, d)
                                if not ok:
                                    sm.start()
                                    sm.fail(error=err)
                                    self._emit(topic_slug, "FAILED", task.task_id, state=state, reason="PATH_TRAVERSAL_REJECTED", error=err)
                                    self._save_state(topic_slug, state)
                                    path_blocked = True
                                    break
                        if path_blocked:
                            continue



                    if safety == "FORBIDDEN":
                        sm.fail(error="Action is FORBIDDEN by ExecutionPolicy.")
                        self._emit(topic_slug, "FAILED", task.task_id,
                                   state=state, reason="FORBIDDEN")
                        self._save_state(topic_slug, state)
                        continue


                    if safety == "REQUIRES_APPROVAL":
                        sm.request_approval()
                        self._save_state(topic_slug, state)
                        self._emit(topic_slug, "REQUIRES_APPROVAL", task.task_id, state=state)

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
                        self._emit(topic_slug, "APPROVED", task.task_id, state=state)

                    else:
                        # SAFE
                        sm.start()
                        self._emit(topic_slug, "STARTED", task.task_id, state=state)
                        summary["executed"].append(task.task_id)

                if task.status != TaskStatus.IN_PROGRESS:
                    continue

                # Execute via ApeCoderAgent if wired, or fall back to standard executor


                try:
                    if self._agent:
                        lineage = {
                            "decision_id": state.decision_id,
                            "policy_decision": state.policy_decision,
                        }
                        res = self._agent.execute_task(
                            task,
                            workspace_context=f"Topic: {topic_slug}",
                            lineage=lineage,
                            sandbox_executor=self._executor,
                            workspace_root=self._root,
                        )

                        # Emit audit logging for each agent step into execution_agent evidence
                        evidence_dir = self._root / ".governance" / "evidence"
                        for step in res.steps:
                            append_to_evidence(
                                evidence_dir,
                                "execution_agent",
                                {
                                    "task_id": task.task_id,
                                    "topic_slug": topic_slug,
                                    "attempt": step.attempt,
                                    "thought": step.thought,
                                    "action": step.action,
                                    "params": step.params,
                                    "exit_code": step.exit_code,
                                    "stdout": step.stdout,
                                    "stderr": step.stderr,
                                    "status": step.status,
                                    "decision_id": state.decision_id,
                                    "policy_decision": state.policy_decision,
                                    "evidence_hash": state.evidence_hash,
                                    "timestamp": _utcnow(),
                                }
                            )

                        if res.status == "FAILED":
                            sm.fail(error=res.error or "Agent execution failed")
                            if task.task_id in summary["executed"]:
                                summary["executed"].remove(task.task_id)
                            self._emit(topic_slug, "FAILED", task.task_id, state=state, error=res.error)
                            self._save_state(topic_slug, state)
                            continue
                        elif res.status == "BLOCKED":
                            sm.block(reason=res.error or "Agent execution blocked")
                            if task.task_id in summary["executed"]:
                                summary["executed"].remove(task.task_id)
                            self._emit(topic_slug, "BLOCKED", task.task_id, state=state, reason=res.error)
                            self._save_state(topic_slug, state)
                            continue
                    else:
                        self._executor.execute(task.description, task.deliverables)
                except RuntimeError as e:
                    if "Docker unavailable" in str(e):
                        sm.block(reason=str(e))
                        if task.task_id in summary["executed"]:
                            summary["executed"].remove(task.task_id)
                        self._emit(topic_slug, "BLOCKED", task.task_id, state=state, reason=str(e))
                        self._save_state(topic_slug, state)
                        continue
                    else:
                        sm.fail(error=str(e))
                        if task.task_id in summary["executed"]:
                            summary["executed"].remove(task.task_id)
                        self._emit(topic_slug, "FAILED", task.task_id, state=state, error=str(e))
                        self._save_state(topic_slug, state)
                        continue

                # Verify deliverables
                ok, missing = self._verifier.verify(task.deliverables)
                if ok:
                    sm.complete()
                    self._emit(topic_slug, "COMPLETED", task.task_id, state=state)
                    self._emit(topic_slug, "VERIFIED", task.task_id,
                               state=state, deliverables=task.deliverables)
                else:
                    sm.fail(error=f"Missing deliverables: {missing}")
                    self._emit(topic_slug, "FAILED", task.task_id,
                               state=state, missing=missing)

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
            self._emit(topic_slug, "PAUSED", "engine", state=state, reason="KeyboardInterrupt")

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
