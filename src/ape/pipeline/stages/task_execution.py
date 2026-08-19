"""TaskExecutionStage — Executes tasks in sequence using TaskStateMachine and TaskExecutor/Agent.

Enforces fail-closed invariants:
- Rejects task execution if path containment is violated (PATH_TRAVERSAL_REJECTED).
- Rejects FORBIDDEN actions according to ExecutionPolicy.
- Orchestrates task execution through TaskStateMachine and returns structured execution summary.

Stage Purity: Orchestrates task execution.
Relies on TaskStateMachine and TaskExecutor as domain services.
Emits governance audit events for task state transitions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ape.intelligence.execution.evaluators import CompositeRuntimeEvaluator
from ape.intelligence.execution.executor import (
    DockerSandboxExecutor,
    SimulationTaskExecutor,
    TaskExecutor,
)
from ape.intelligence.execution.intervention import (
    GovernedInterventionPolicy,
    InterventionAction,
)
from ape.intelligence.execution.models import (
    ExecutionState,
    ExecutionStatus,
    ExecutionTask,
    TaskStatus,
)
from ape.intelligence.execution.policy import ExecutionPolicy, validate_path_containment
from ape.intelligence.execution.state import TaskStateMachine
from ape.intelligence.execution.trajectory import ExecutionTrajectory, TrajectoryStep
from ape.pipeline.contracts import (
    BasePipelineContext,
    ExecutionContext,
    PipelineStage,
    StageResult,
    StageStatus,
)
from ape.utils import append_to_evidence


class TaskExecutionStage(PipelineStage):
    """Pipeline stage that orchestrates task queue execution."""

    def __init__(
        self,
        project_root: Path,
        executor: Optional[TaskExecutor] = None,
        agent: Optional[Any] = None,
    ) -> None:
        self._root = project_root
        self._custom_executor = executor
        self._agent = agent
        self._policy = ExecutionPolicy()

    @property
    def name(self) -> str:
        return "task_execution"

    def _emit(
        self,
        topic_slug: str,
        event: str,
        task_id: str,
        state: Optional[ExecutionState] = None,
        **extra: Any,
    ) -> None:
        lineage = {}
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **lineage,
            **extra,
        }
        append_to_evidence(self._root / ".governance" / "evidence", "execution", payload)

    def execute(
        self,
        context: BasePipelineContext,
        previous_results: List[StageResult],
    ) -> StageResult:
        if not isinstance(context, ExecutionContext):
            dry_run = getattr(context, "dry_run", True)
            topic_slug = getattr(context, "topic_slug", "unknown")
            auto_deny = getattr(context, "auto_deny_approvals", False)
            interrupt_after = getattr(context, "interrupt_after_tasks", None)
        else:
            dry_run = context.dry_run
            topic_slug = context.topic_slug
            auto_deny = context.auto_deny_approvals
            interrupt_after = context.interrupt_after_tasks

        # Retrieve state and tasks from previous Plan, Policy, and Capability stages
        raw_tasks: List[Dict[str, Any]] = []
        existing_state_dict: Optional[Dict[str, Any]] = None
        execution_backend = "simulation" if dry_run else "docker"
        decision_id = "UNKNOWN"
        policy_decision = "UNKNOWN"
        evidence_hash = ""

        for prev in previous_results:
            if prev.stage_name == "execution_plan":
                raw_tasks = prev.output_data.get("tasks", [])
                existing_state_dict = prev.output_data.get("existing_state")
            elif prev.stage_name == "policy_gate":
                decision_id = prev.output_data.get("decision_id", "UNKNOWN")
                policy_decision = prev.output_data.get("policy_decision", "UNKNOWN")
                evidence_hash = prev.output_data.get("evidence_hash", "")
            elif prev.stage_name == "capability_check":
                execution_backend = prev.output_data.get("execution_backend", execution_backend)

        # Instantiate executor
        if self._custom_executor:
            executor = self._custom_executor
        elif dry_run or execution_backend == "simulation":
            executor = SimulationTaskExecutor()
        else:
            executor = DockerSandboxExecutor(evidence_dir=self._root / ".governance" / "evidence")

        # Build or rehydrate tasks & ExecutionState
        if existing_state_dict:
            state = ExecutionState.from_dict(existing_state_dict)
            if decision_id != "UNKNOWN" and not state.decision_id:
                state.decision_id = decision_id
                state.policy_decision = policy_decision
                state.evidence_hash = evidence_hash
        else:
            tasks_list = [
                ExecutionTask(
                    task_id=t["task_id"],
                    description=t.get("description", ""),
                    deliverables=t.get("deliverables", []),
                    action=t.get("action", "create_file"),
                )
                for t in raw_tasks
            ]
            state = ExecutionState(
                execution_id=f"exec_stage_{topic_slug}",
                roadmap_id="roadmap_stage",
                decision_id=decision_id,
                policy_decision=policy_decision,
                evidence_hash=evidence_hash,
                topic=topic_slug,
                tasks=tasks_list,
            )

        trajectory = ExecutionTrajectory(
            execution_id=state.execution_id,
            topic_slug=topic_slug,
            decision_id=state.decision_id or decision_id,
            policy_decision=state.policy_decision or policy_decision,
            evidence_hash=state.evidence_hash or evidence_hash,
        )

        summary: Dict[str, List[str]] = {
            "executed": [],
            "retried": [],
            "skipped": [],
            "paused": [],
        }
        agent_steps: List[Dict[str, Any]] = []
        tasks_run = 0
        execution_error: Optional[str] = None

        try:
            for task in state.tasks:
                sm = TaskStateMachine(task)

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
                    safety = self._policy.classify(task.action)

                    # Check path containment for deliverable targets
                    if task.action in ("create_file", "modify_file"):
                        path_blocked = False
                        for d in task.deliverables:
                            if d and isinstance(d, str):
                                ok, err = validate_path_containment(self._root, d)
                                if not ok:
                                    sm.start()
                                    sm.fail(error=err)
                                    self._emit(
                                        topic_slug,
                                        "FAILED",
                                        task.task_id,
                                        state=state,
                                        reason="PATH_TRAVERSAL_REJECTED",
                                        error=err,
                                    )
                                    path_blocked = True
                                    execution_error = f"Path containment rejected: {err}"
                                    break
                        if path_blocked:
                            continue

                    if safety == "FORBIDDEN":
                        sm.fail(error="Action is FORBIDDEN by ExecutionPolicy.")
                        self._emit(
                            topic_slug,
                            "FAILED",
                            task.task_id,
                            state=state,
                            reason="FORBIDDEN",
                        )
                        execution_error = "Action is FORBIDDEN by ExecutionPolicy."
                        continue

                    if safety == "REQUIRES_APPROVAL":
                        sm.request_approval()
                        self._emit(topic_slug, "REQUIRES_APPROVAL", task.task_id, state=state)
                        if auto_deny or dry_run:
                            sm.deny(reason="AUTO_DENIED")
                            self._emit(
                                topic_slug,
                                "DENIED",
                                task.task_id,
                                state=state,
                                reason="AUTO_DENIED",
                            )
                            continue
                        sm.approve()
                        self._emit(topic_slug, "APPROVED", task.task_id, state=state)

                    # SAFE / APPROVED
                    sm.start()
                    self._emit(topic_slug, "STARTED", task.task_id, state=state)
                    summary["executed"].append(task.task_id)

                if task.status != TaskStatus.IN_PROGRESS:
                    continue

                # Execute task via Agent or Executor with Governance Authorization Token
                try:
                    from ape.pipeline.stages.policy_gate import PolicyGateStage
                    auth_token = PolicyGateStage.issue_execution_token(task.task_id)

                    if self._agent:
                        lineage = {
                            "decision_id": state.decision_id,
                            "policy_decision": state.policy_decision,
                        }
                        res = self._agent.execute_task(
                            task,
                            workspace_context=f"Topic: {topic_slug}",
                            lineage=lineage,
                            sandbox_executor=executor,
                            workspace_root=self._root,
                            auth_token=auth_token,
                        )

                        for step in res.steps:
                            import hashlib as _hashlib

                            out_bytes = (step.stdout or "").encode("utf-8")
                            stdout_h = _hashlib.sha256(out_bytes).hexdigest()
                            raw_err = step.stderr or getattr(step, "error", None) or ""
                            stderr_sig = raw_err.strip().split("\n")[0][:100]

                            ts_step = TrajectoryStep(
                                step_id=f"step_{task.task_id}_{step.attempt}",
                                task_id=task.task_id,
                                attempt=step.attempt,
                                thought=step.thought,
                                action=step.action,
                                params=step.params,
                                exit_code=step.exit_code,
                                stdout_hash=stdout_h,
                                stderr_signature=stderr_sig,
                                status=step.status,
                                timestamp=datetime.now(timezone.utc).isoformat(),
                            )
                            trajectory.append_step(ts_step)

                            agent_steps.append({
                                "task_id": task.task_id,
                                "thought": step.thought,
                                "action": step.action,
                                "status": step.status,
                            })
                            step_payload = {
                                "event": "AGENT_STEP",
                                "topic_slug": topic_slug,
                                "task_id": task.task_id,
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
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                            evidence_dir = self._root / ".governance" / "evidence"
                            append_to_evidence(evidence_dir, "execution_agent", step_payload)

                        if res.status == "FAILED":
                            sm.fail(error=res.error or "Agent execution failed")
                            self._emit(
                                topic_slug,
                                "FAILED",
                                task.task_id,
                                state=state,
                                error=res.error,
                            )
                            if task.task_id in summary["executed"]:
                                summary["executed"].remove(task.task_id)
                            execution_error = res.error or "Agent execution failed"
                            continue
                        else:
                            sm.complete()
                            self._emit(topic_slug, "COMPLETED", task.task_id, state=state)
                    else:
                        if not dry_run:
                            raise RuntimeError("Production execution requires an active Agent. Agentless execution fallback is forbidden in non-simulation environments.")
                        try:
                            executor.execute(
                                task.description,
                                task.deliverables,
                                workspace_root=self._root,
                                dry_run=dry_run,
                            )
                        except TypeError:
                            executor.execute(task.description, task.deliverables)
                        sm.complete()
                        self._emit(topic_slug, "COMPLETED", task.task_id, state=state)
                except Exception as exc:
                    sm.fail(error=str(exc))
                    self._emit(topic_slug, "FAILED", task.task_id, state=state, error=str(exc))
                    if task.task_id in summary["executed"]:
                        summary["executed"].remove(task.task_id)
                    execution_error = str(exc)
                    continue

                tasks_run += 1
                if interrupt_after and tasks_run >= interrupt_after:
                    raise KeyboardInterrupt

        except KeyboardInterrupt:
            import json as _json
            for task in state.tasks:
                if task.status == TaskStatus.IN_PROGRESS:
                    TaskStateMachine(task).pause()
                    summary["paused"].append(task.task_id)
            state.status = ExecutionStatus.PAUSED

            state_dir = self._root / ".build" / "execution" / topic_slug
            state_dir.mkdir(parents=True, exist_ok=True)
            formatted_json = _json.dumps(state.to_dict(), indent=2)
            (state_dir / "current.json").write_text(formatted_json, encoding="utf-8")

            self._emit(topic_slug, "PAUSED", "engine", state=state, reason="KeyboardInterrupt")
            return StageResult(
                stage_name=self.name,
                status=StageStatus.BLOCKED,
                error="Task execution interrupted by user (KeyboardInterrupt).",
                output_data={
                    "execution_summary": summary,
                    "agent_steps": agent_steps,
                    "state": state.to_dict(),
                    "status": "PAUSED",
                },
                evidence={
                    "failure_reason": "KEYBOARD_INTERRUPT",
                    "execution_summary": summary,
                },
            )

        any_failed = any(t.status in (TaskStatus.FAILED, TaskStatus.DENIED) for t in state.tasks)
        all_completed = all(t.status == TaskStatus.COMPLETED for t in state.tasks)
        if all_completed:
            state.status = ExecutionStatus.COMPLETED
        elif any_failed:
            state.status = ExecutionStatus.FAILED
        else:
            state.status = ExecutionStatus.IN_PROGRESS

        # Run deterministic supervisory evaluators over execution trajectory
        evaluator = CompositeRuntimeEvaluator()
        health_signals = evaluator.evaluate(trajectory)
        serialized_signals = [sig.to_dict() for sig in health_signals]

        # Resolve governed adaptive intervention policy
        intervention_policy = GovernedInterventionPolicy()
        intervention_proposal = intervention_policy.resolve(health_signals)

        output_data = {
            "execution_summary": summary,
            "agent_steps": agent_steps,
            "trajectory": trajectory.to_dict(),
            "health_signals": serialized_signals,
            "intervention_proposal": intervention_proposal.to_dict(),
            "state": state.to_dict(),
            "tasks_executed_count": len(summary["executed"]),
            "status": state.status.value,
        }

        evidence = {
            "execution_summary": summary,
            "agent_steps_count": len(agent_steps),
            "trajectory_hash": trajectory.compute_trajectory_hash(),
            "health_signals_count": len(health_signals),
            "intervention_action": intervention_proposal.proposed_action.value,
            "state_status": state.status.value,
        }

        # Persist execution state to disk (with dry-run sentinel protection)
        import json as _json
        state_dir = self._root / ".build" / "execution" / topic_slug
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "current.json"

        should_write = True
        if dry_run and state_file.exists():
            try:
                existing = _json.loads(state_file.read_text(encoding="utf-8"))
                if existing.get("sentinel"):
                    should_write = False
            except Exception:
                pass

        if should_write:
            state_file.write_text(_json.dumps(state.to_dict(), indent=2), encoding="utf-8")

        stage_status = StageStatus.FAILED if any_failed else StageStatus.SUCCESS
        if intervention_proposal.proposed_action == InterventionAction.SAFE_HOLD:
            stage_status = StageStatus.BLOCKED
            execution_error = intervention_proposal.reason
        elif intervention_proposal.proposed_action == InterventionAction.ABORT:
            stage_status = StageStatus.FAILED
            execution_error = intervention_proposal.reason

        return StageResult(
            stage_name=self.name,
            status=stage_status,
            error=execution_error,
            output_data=output_data,
            evidence=evidence,
        )
