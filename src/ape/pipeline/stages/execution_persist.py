"""ExecutionPersistStage — Persists execution state and appends immutable governance evidence logs.

Enforces Fail-Closed Invariants:
- Fail-Closed Governance: If appending audit evidence log fails, execution is NOT marked success.
- State Immutability & Sentinel Protection: Respects dry-run sentinel states.

Stage Purity: Handles persistence boundary; writes mutable state and append-only evidence logs.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ape.pipeline.contracts import (
    BasePipelineContext,
    ExecutionContext,
    PipelineStage,
    StageResult,
    StageStatus,
)
from ape.utils import append_to_evidence


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutionPersistStage(PipelineStage):
    """Pipeline stage responsible for persisting state and audit evidence."""

    def __init__(self, project_root: Path) -> None:
        self._root = project_root

    @property
    def name(self) -> str:
        return "execution_persist"

    def execute(
        self,
        context: BasePipelineContext,
        previous_results: List[StageResult],
    ) -> StageResult:
        if not isinstance(context, ExecutionContext):
            topic_slug = getattr(context, "topic_slug", "unknown")
            dry_run = getattr(context, "dry_run", True)
        else:
            topic_slug = context.topic_slug
            dry_run = context.dry_run

        state_dict: Optional[Dict[str, Any]] = None
        evidence_bundle: Optional[Dict[str, Any]] = None

        for prev in previous_results:
            if prev.stage_name == "task_execution" and "state" in prev.output_data:
                state_dict = prev.output_data["state"]
            elif prev.stage_name == "execution_evidence" and "evidence_bundle" in prev.output_data:
                evidence_bundle = prev.output_data["evidence_bundle"]

        if not state_dict:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error="ExecutionPersistStage missing state_dict from previous stage.",
                evidence={"failure_reason": "STATE_DICT_MISSING"},
            )

        state_updated = False
        audit_appended = False
        state_checksum = ""

        # 1. Write Mutable Canonical State: .build/execution/<topic_slug>/current.json
        try:
            state_dir = self._root / ".build" / "execution" / topic_slug
            state_dir.mkdir(parents=True, exist_ok=True)
            state_file = state_dir / "current.json"

            # Sentinel protection check in dry-run
            should_write = True
            if dry_run and state_file.exists():
                try:
                    existing = json.loads(state_file.read_text(encoding="utf-8"))
                    if existing.get("sentinel"):
                        should_write = False
                except Exception:
                    pass

            state_dict["updated_at"] = _utcnow()
            raw_state_json = json.dumps(state_dict, indent=2)
            state_checksum = hashlib.sha256(raw_state_json.encode("utf-8")).hexdigest()

            if should_write:
                state_file.write_text(raw_state_json, encoding="utf-8")
            state_updated = True
        except Exception as exc:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error=f"Failed to persist state file for '{topic_slug}': {exc}",
                evidence={"failure_reason": "STATE_PERSIST_FAILED"},
            )

        # 2. Write Immutable Governance Log: .governance/evidence/execution-YYYY-MM.jsonl
        try:
            evidence_dir = self._root / ".governance" / "evidence"
            decision_id = state_dict.get("decision_id") or (evidence_bundle.get("policy_info", {}).get("decision_id") if evidence_bundle else "UNKNOWN")
            policy_decision = state_dict.get("policy_decision") or (evidence_bundle.get("policy_info", {}).get("policy_decision") if evidence_bundle else "UNKNOWN")
            evidence_hash = state_dict.get("evidence_hash", "")

            # SPEC-0019 INV-4 (dual-channel): include ResourceUsage from context metadata
            # if the runner has populated it. Defaults to empty dict when unavailable.
            resource_usage_payload: Dict[str, Any] = (
                context.metadata.get("resource_usage", {})
                if isinstance(getattr(context, "metadata", None), dict)
                else {}
            )

            payload = {
                "event": "PIPELINE_EXECUTION_COMPLETED",
                "topic_slug": topic_slug,
                "timestamp": _utcnow(),
                "state_checksum": state_checksum,
                "decision_id": decision_id,
                "policy_decision": policy_decision,
                "evidence_hash": evidence_hash,
                "evidence_bundle": evidence_bundle or {},
                "resource_usage": resource_usage_payload,
            }
            append_to_evidence(evidence_dir, "execution", payload)
            audit_appended = True
        except Exception as exc:
            # Constitutional Rule: No evidence, no execution success!
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error=f"Fail-Closed Governance: Audit log append failed for '{topic_slug}': {exc}",
                evidence={"failure_reason": "AUDIT_APPEND_FAILED"},
            )

        persist_receipt = {
            "timestamp": _utcnow(),
            "state_updated": state_updated,
            "audit_appended": audit_appended,
            "state_checksum": state_checksum,
            "persist_version": 1,
        }

        output_data = {
            "persist_receipt": persist_receipt,
            "state_persisted": True,
            "audit_appended": True,
        }

        evidence = {
            "state_checksum": state_checksum,
            "state_updated": state_updated,
            "audit_appended": audit_appended,
        }

        return StageResult(
            stage_name=self.name,
            status=StageStatus.SUCCESS,
            output_data=output_data,
            evidence=evidence,
        )
