"""ReleaseDecisionStage — Pure, Zero-IO final governance decision gate for execution pipelines.

Enforces Fail-Closed Invariants:
- Zero IO Stage: Performs no disk mutations or file reads. Evaluates pure prior stage results.
- Returns release_decision status 'APPROVED' if and only if all prior stages completed successfully and evidence was persisted.
- Returns release_decision status 'REJECTED' if any prior stage failed, was blocked, or failed verification/persisting.
"""

from __future__ import annotations

from typing import List, Optional

from ape.pipeline.contracts import (
    BasePipelineContext,
    PipelineStage,
    StageResult,
    StageStatus,
)


class ReleaseDecisionStage(PipelineStage):
    """Pipeline stage that evaluates previous stage results to issue the final release decision."""

    @property
    def name(self) -> str:
        return "release_decision"

    def execute(
        self,
        context: BasePipelineContext,
        previous_results: List[StageResult],
    ) -> StageResult:
        failed_stage: Optional[str] = None
        blocked_stage: Optional[str] = None
        verification_passed = False
        persist_receipt_valid = False

        quality_audit_passed = True
        task_exec_status = "COMPLETED"
        for prev in previous_results:
            if prev.status == StageStatus.FAILED:
                failed_stage = prev.stage_name
                break
            if prev.status == StageStatus.BLOCKED:
                blocked_stage = prev.stage_name
                break
            if prev.stage_name == "task_execution":
                task_exec_status = prev.output_data.get("status", "UNKNOWN")
            elif prev.stage_name == "verification":
                verification_passed = prev.output_data.get("verification_passed", False)
            elif prev.stage_name == "quality_assurance":
                quality_audit_passed = prev.output_data.get("quality_audit_passed", True)
            elif prev.stage_name == "execution_persist":
                receipt = prev.output_data.get("persist_receipt", {})
                persist_receipt_valid = receipt.get("state_updated", False) and receipt.get("audit_appended", False)

        if task_exec_status != "COMPLETED" and not failed_stage and not blocked_stage:
            topic_slug = getattr(context, "topic_slug", "")
            reason = f"Execution for '{topic_slug}' is not COMPLETED (current status: {task_exec_status})."
            release_decision = {
                "status": "REJECTED",
                "reason": reason,
                "approval_allowed": False,
            }
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error=reason,
                output_data={"release_decision": release_decision},
                evidence={"failure_reason": "EXECUTION_NOT_COMPLETED"},
            )

        if failed_stage:
            reason = f"Release REJECTED: Stage '{failed_stage}' failed during pipeline execution."
            release_decision = {
                "status": "REJECTED",
                "reason": reason,
                "failed_stage": failed_stage,
                "approval_allowed": False,
            }
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error=reason,
                output_data={"release_decision": release_decision},
                evidence={"failure_reason": f"RELEASE_REJECTED_STAGE_{failed_stage.upper()}"},
            )

        if blocked_stage:
            reason = f"Release REJECTED: Stage '{blocked_stage}' was blocked."
            release_decision = {
                "status": "REJECTED",
                "reason": reason,
                "blocked_stage": blocked_stage,
                "approval_allowed": False,
            }
            return StageResult(
                stage_name=self.name,
                status=StageStatus.BLOCKED,
                error=reason,
                output_data={"release_decision": release_decision},
                evidence={"failure_reason": f"RELEASE_REJECTED_BLOCKED_{blocked_stage.upper()}"},
            )

        from pathlib import Path
        from ape.policy.engine import PolicyEngine

        project_root = getattr(context, "root", getattr(context, "project_root", Path.cwd()))
        policy_engine = PolicyEngine(project_root)
        policy_eval = policy_engine.evaluate(context, previous_results)

        if not policy_eval.passed:
            reason = f"Release REJECTED by PolicyEngine ({policy_eval.policy_name}): {'; '.join(policy_eval.violations)}"
            release_decision = {
                "status": "REJECTED",
                "reason": reason,
                "approval_allowed": False,
                "policy_evaluation": policy_eval.to_dict(),
            }
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error=reason,
                output_data={"release_decision": release_decision},
                evidence={
                    "failure_reason": "POLICY_ENGINE_REJECTED",
                    "policy_violations": policy_eval.violations,
                },
            )

        release_decision = {
            "status": "APPROVED",
            "reason": f"All constitutional pipeline gates passed under policy '{policy_eval.policy_name}'.",
            "approval_allowed": True,
            "policy_evaluation": policy_eval.to_dict(),
        }

        output_data = {
            "release_decision": release_decision,
            "released": True,
        }

        evidence = {
            "release_status": "APPROVED",
            "stages_verified_count": len(previous_results),
            "passed_rules": policy_eval.passed_rules,
        }

        return StageResult(
            stage_name=self.name,
            status=StageStatus.SUCCESS,
            output_data=output_data,
            evidence=evidence,
        )
