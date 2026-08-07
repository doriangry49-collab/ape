"""ExecutionEvidenceStage — Pure Evidence Collector for execution pipelines.

Enforces Stage Purity:
- Does NOT perform disk IO or append to evidence files.
- Aggregates evidence and metrics from prior stages (plan, policy, capability, execution, verification).
- Produces a pure, deterministic EvidenceBundle payload for downstream persistence.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ape.pipeline.contracts import (
    BasePipelineContext,
    ExecutionContext,
    PipelineStage,
    StageResult,
    StageStatus,
)


class ExecutionEvidenceStage(PipelineStage):
    """Pipeline stage that collects evidence from all execution stages into a pure bundle."""

    @property
    def name(self) -> str:
        return "execution_evidence"

    def execute(
        self,
        context: BasePipelineContext,
        previous_results: List[StageResult],
    ) -> StageResult:
        if not isinstance(context, ExecutionContext):
            topic_slug = getattr(context, "topic_slug", "unknown")
            run_id = getattr(context, "run_id", "unknown")
        else:
            topic_slug = context.topic_slug
            run_id = context.run_id

        stage_hashes: Dict[str, str] = {}
        plan_summary: Dict[str, Any] = {}
        policy_info: Dict[str, Any] = {}
        environment_snapshot: Dict[str, Any] = {}
        execution_summary: Dict[str, Any] = {}
        verification_summary: Dict[str, Any] = {}
        quality_summary: Dict[str, Any] = {}

        for prev in previous_results:
            stage_hashes[prev.stage_name] = prev.evidence.get("stage_hash", "")
            if prev.stage_name == "execution_plan":
                plan_summary = prev.output_data.get("execution_plan", {})
            elif prev.stage_name == "policy_gate":
                policy_info = {
                    "policy_decision": prev.output_data.get("policy_decision", "UNKNOWN"),
                    "decision_id": prev.output_data.get("decision_id", "UNKNOWN"),
                    "decision_score": prev.output_data.get("decision_score", 0),
                }
            elif prev.stage_name == "capability_check":
                environment_snapshot = prev.output_data.get("environment_snapshot", {})
            elif prev.stage_name == "task_execution":
                execution_summary = prev.output_data.get("execution_summary", {})
            elif prev.stage_name == "verification":
                verification_summary = {
                    "verification_passed": prev.output_data.get("verification_passed", False),
                    "verified_deliverables": prev.output_data.get("verified_deliverables", []),
                }
            elif prev.stage_name == "quality_assurance":
                quality_summary = {
                    "quality_audit_passed": prev.output_data.get("quality_audit_passed", False),
                    "overall_score": prev.output_data.get("overall_score", 0.0),
                    "quality_report": prev.output_data.get("quality_report", {}),
                }

        evidence_bundle = {
            "run_id": run_id,
            "topic_slug": topic_slug,
            "plan_summary": plan_summary,
            "policy_info": policy_info,
            "environment_snapshot": environment_snapshot,
            "execution_summary": execution_summary,
            "verification_summary": verification_summary,
            "quality_summary": quality_summary,
            "stage_hashes": stage_hashes,
        }

        output_data = {
            "evidence_bundle": evidence_bundle,
            "bundle_created": True,
        }

        evidence = {
            "stages_aggregated": list(stage_hashes.keys()),
            "run_id": run_id,
            "topic_slug": topic_slug,
        }

        return StageResult(
            stage_name=self.name,
            status=StageStatus.SUCCESS,
            output_data=output_data,
            evidence=evidence,
        )
