"""VerificationStage — Verifies task deliverables and execution outputs.

Enforces fail-closed invariants:
- Fails (FAILED) if required task deliverables are missing on disk during live execution.
- Verifies output integrity using DeliverableVerifier.

Stage Purity: Read-only verification stage. Performs deliverable checks and returns verification results.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from ape.intelligence.execution.verifier import DeliverableVerifier
from ape.pipeline.contracts import (
    BasePipelineContext,
    ExecutionContext,
    PipelineStage,
    StageResult,
    StageStatus,
)
from ape.quality.contracts import ValidationContext
from ape.quality.runner import QualityRunner


class VerificationStage(PipelineStage):
    """Pipeline stage that verifies deliverable integrity and Quality OS validation rules."""

    def __init__(
        self,
        project_root: Path,
        verifier: Optional[DeliverableVerifier] = None,
        quality_runner: Optional[QualityRunner] = None,
    ) -> None:
        self._root = project_root
        self._custom_verifier = verifier
        self._quality_runner = quality_runner or QualityRunner()

    @property
    def name(self) -> str:
        return "verification"

    def execute(
        self,
        context: BasePipelineContext,
        previous_results: List[StageResult],
    ) -> StageResult:
        if not isinstance(context, ExecutionContext):
            dry_run = getattr(context, "dry_run", True)
        else:
            dry_run = context.dry_run

        verifier = self._custom_verifier or DeliverableVerifier(self._root, dry_run=dry_run)

        # Collect deliverables from previous Plan/Execution stages
        deliverables: List[str] = []
        for prev in previous_results:
            if prev.stage_name == "execution_plan" and "tasks" in prev.output_data:
                for t in prev.output_data["tasks"]:
                    deliverables.extend(t.get("deliverables", []))

        # Perform deliverable existence verification via DeliverableVerifier
        ok, missing = verifier.verify(deliverables)

        if not ok:
            error_msg = f"Verification FAILED: Missing deliverables: {missing}"
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error=error_msg,
                output_data={
                    "verification_passed": False,
                    "verified_deliverables": [d for d in deliverables if d not in missing],
                    "missing_deliverables": missing,
                },
                evidence={
                    "failure_reason": "MISSING_DELIVERABLES",
                    "missing_deliverables": missing,
                },
            )

        # Run Quality OS Validation Engine
        # Infer src_root: if any deliverable lives under .../src/..., extract that src/ dir.
        # This lets validators inject the correct PYTHONPATH for src/-layout packages.
        src_root = None
        for d in deliverables:
            parts = Path(d).parts
            if "src" in parts:
                src_idx = parts.index("src")
                candidate = self._root / Path(*parts[:src_idx + 1])
                if candidate.is_dir():
                    src_root = candidate
                    break

        val_ctx = ValidationContext(
            project_root=self._root,
            topic_slug=getattr(context, "topic", "deliverable"),
            deliverables=deliverables,
            dry_run=dry_run,
            src_root=src_root,
        )
        quality_report = self._quality_runner.run(val_ctx)

        quality_passed = quality_report.quality_audit_passed
        stage_status = StageStatus.SUCCESS if quality_passed else StageStatus.FAILED
        error_msg = None if quality_passed else f"Quality OS Audit FAILED: Overall Score {quality_report.overall_score}"

        output_data = {
            "verification_passed": quality_passed,
            "verified_deliverables": deliverables,
            "missing_deliverables": [],
            "quality_report": quality_report.to_dict(),
        }

        evidence = {
            "verified_count": len(deliverables),
            "verification_passed": quality_passed,
            "quality_score": quality_report.overall_score,
            "quality_merkle_root": quality_report.evidence_manifest.get("quality_merkle_root", ""),
            "evidence_manifest": quality_report.evidence_manifest,
            "quality_report": quality_report.to_dict(),
        }

        return StageResult(
            stage_name=self.name,
            status=stage_status,
            error=error_msg,
            output_data=output_data,
            evidence=evidence,
        )
