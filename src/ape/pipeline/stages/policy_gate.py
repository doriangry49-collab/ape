"""PolicyGateStage — Enforces SPEC-0014 policy decision verification for execution pipelines.

Enforces fail-closed invariants:
- Fails (FAILED) if policy decision artifact is missing for the specified topic_slug.
- Blocks (BLOCKED) if policy decision is WATCH, IGNORE, or BLOCKED. Only BUILD and VALIDATE may proceed.

Architecture: Uses DecisionRepository abstraction for accessing decision artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ape.intelligence.execution.exceptions import PolicyExecutionBlockedError
from ape.pipeline.contracts import (
    BasePipelineContext,
    ExecutionContext,
    PipelineStage,
    StageResult,
    StageStatus,
)
from ape.utils import get_current_artifact


class DecisionRepository:
    """Repository abstraction for fetching decision artifacts (decoupled from storage layout)."""

    def __init__(self, project_root: Path) -> None:
        self._root = project_root

    def get_decision(self, topic_slug: str) -> Optional[Dict[str, Any]]:
        """Fetches and parses the decision artifact for topic_slug. Returns None if missing."""
        decisions_dir = self._root / ".build" / "decisions"
        decision_file = get_current_artifact(decisions_dir, topic_slug)
        if not decision_file or not decision_file.exists():
            return None
        try:
            return json.loads(decision_file.read_text(encoding="utf-8"))
        except Exception:
            return None


class PolicyGateStage(PipelineStage):
    """Pipeline stage that enforces policy gates (SPEC-0014) fast-fail before capability/execution."""

    def __init__(
        self,
        project_root: Path,
        repository: Optional[DecisionRepository] = None,
    ) -> None:
        self._root = project_root
        self._repository = repository or DecisionRepository(project_root)

    @property
    def name(self) -> str:
        return "policy_gate"

    def execute(
        self,
        context: BasePipelineContext,
        previous_results: List[StageResult],
    ) -> StageResult:
        if not isinstance(context, ExecutionContext):
            topic_slug = getattr(context, "topic_slug", "")
        else:
            topic_slug = context.topic_slug

        if not topic_slug or not topic_slug.strip():
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error="Invalid or empty topic_slug provided in context.",
                evidence={"failure_reason": "INVALID_TOPIC_SLUG"},
            )

        # 1. Fetch decision artifact via DecisionRepository abstraction
        decision_data = self._repository.get_decision(topic_slug)
        if not decision_data:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error=f"No decision artifact found for topic_slug: '{topic_slug}'. Run `ape decide` first.",
                evidence={"failure_reason": "DECISION_ARTIFACT_MISSING"},
            )

        decision_val = str(decision_data.get("decision", "")).upper()
        decision_id = decision_data.get("decision_id", "UNKNOWN")
        evidence_hash = decision_data.get("evidence_hash", "")
        decision_score = decision_data.get("score", decision_data.get("confidence_score", 0))
        decision_reason = decision_data.get("reason", decision_data.get("narrative", "No reason provided"))
        approval_required = decision_data.get("approval_required", False)

        # 2. Fast-Fail Gate Check (SPEC-0014 §3)
        if decision_val in ("WATCH", "IGNORE", "BLOCKED"):
            error_msg = (
                f"Execution blocked: PolicyDecision is '{decision_val}'. "
                "Only BUILD or VALIDATE decisions may be executed. (SPEC-0014 §3)"
            )
            return StageResult(
                stage_name=self.name,
                status=StageStatus.BLOCKED,
                error=error_msg,
                output_data={
                    "policy_decision": decision_val,
                    "decision_id": decision_id,
                    "evidence_hash": evidence_hash,
                    "decision_score": decision_score,
                    "decision_reason": decision_reason,
                    "approval_required": approval_required,
                },
                evidence={
                    "failure_reason": f"POLICY_DECISION_{decision_val}",
                    "policy_decision": decision_val,
                    "decision_id": decision_id,
                },
            )

        if decision_val not in ("BUILD", "VALIDATE"):
            error_msg = f"Unknown or invalid PolicyDecision '{decision_val}' for topic '{topic_slug}'."
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error=error_msg,
                evidence={"failure_reason": "INVALID_POLICY_DECISION"},
            )

        output_data = {
            "policy_decision": decision_val,
            "decision_id": decision_id,
            "evidence_hash": evidence_hash,
            "decision_score": decision_score,
            "decision_reason": decision_reason,
            "approval_required": approval_required,
            "decision_raw": decision_data,
        }

        evidence = {
            "policy_decision": decision_val,
            "decision_id": decision_id,
            "evidence_hash": evidence_hash,
            "topic_slug": topic_slug,
        }

        return StageResult(
            stage_name=self.name,
            status=StageStatus.SUCCESS,
            output_data=output_data,
            evidence=evidence,
        )
