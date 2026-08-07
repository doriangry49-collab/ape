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
from ape.pipeline.contracts import ExecutionContext, StageStatus
from ape.pipeline.runner import PipelineExecutionError
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

    def _build_pipeline(self) -> ConstitutionalPipelineRunner:
        """Constructs the constitutional 8-stage ExecutionPipeline."""
        from ape.pipeline.runner import ConstitutionalPipelineRunner
        from ape.pipeline.stages.execution_plan import ExecutionPlanStage
        from ape.pipeline.stages.policy_gate import PolicyGateStage
        from ape.pipeline.stages.capability_check import CapabilityCheckStage
        from ape.pipeline.stages.task_execution import TaskExecutionStage
        from ape.pipeline.stages.verification import VerificationStage
        from ape.pipeline.stages.execution_evidence import ExecutionEvidenceStage
        from ape.pipeline.stages.execution_persist import ExecutionPersistStage
        from ape.pipeline.stages.quality_assurance import QualityAssuranceStage
        from ape.pipeline.stages.release_decision import ReleaseDecisionStage

        return ConstitutionalPipelineRunner([
            ExecutionPlanStage(self._root),
            PolicyGateStage(self._root),
            CapabilityCheckStage(self._root),
            TaskExecutionStage(self._root, executor=self._executor, agent=self._agent),
            VerificationStage(self._root, verifier=self._verifier),
            QualityAssuranceStage(),
            ExecutionEvidenceStage(),
            ExecutionPersistStage(self._root),
            ReleaseDecisionStage(),
        ])

    def execute(self, topic: str, topic_slug: str) -> dict:
        """
        Main entry point for `ape execute` powered by ConstitutionalPipelineRunner.
        """
        # Enforce RFC-014 exception semantics for backwards compatibility
        decision_data = self._verify_decision_gate(topic_slug)

        ctx = ExecutionContext(
            run_id=f"run_exec_{uuid.uuid4().hex[:8]}",
            topic_slug=topic_slug,
            topic=topic,
            dry_run=self._dry_run,
            auto_deny_approvals=self._auto_deny,
            interrupt_after_tasks=self._interrupt_after,
        )

        pipeline = self._build_pipeline()
        try:
            results = pipeline.run(ctx)
        except PipelineExecutionError as p_err:
            if p_err.stage_result.stage_name == "execution_plan" and p_err.stage_result.status == StageStatus.FAILED:
                raise FileNotFoundError(f"Roadmap not found for: {topic_slug}. Run `ape plan` first.")
            if p_err.stage_result.stage_name in ("task_execution", "verification", "release_decision"):
                for res in [p_err.stage_result, *getattr(p_err, "previous_results", [])]:
                    if getattr(res, "stage_name", "") == "task_execution":
                        return res.output_data.get("execution_summary", {"executed": [], "retried": [], "skipped": [], "paused": []})
            raise

        summary = {"executed": [], "retried": [], "skipped": [], "paused": []}
        for res in results:
            if res.stage_name == "task_execution":
                summary = res.output_data.get("execution_summary", summary)
                break

        return summary

    def resume_or_start(self, topic_slug: str) -> dict:
        """
        Resume from an existing ExecutionState using ConstitutionalPipelineRunner.
        """
        decision_data = self._verify_decision_gate(topic_slug)

        state = self._load_state(topic_slug)
        if state is None:
            return {"executed": [], "retried": [], "skipped": [], "paused": []}

        if decision_data and state.decision_id != decision_data.get("decision_id"):
            raise LineageMismatchError(
                f"Lineage mismatch on resume: ExecutionState decision_id '{state.decision_id}' "
                f"does not match current artifact decision_id '{decision_data.get('decision_id')}'. "
                "Cannot resume."
            )

        return self.execute(topic=state.topic, topic_slug=topic_slug)

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
            return None

    def _verify_decision_gate(self, topic_slug: str) -> dict:
        """
        RFC-014 Policy Gate: reads the decision artifact and blocks execution
        for WATCH, IGNORE, or BLOCKED decisions.
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
