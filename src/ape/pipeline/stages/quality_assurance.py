"""
QualityAssuranceStage — 9th Stage in Constitutional Execution Pipeline.
Evaluates deliverable files using language-agnostic Quality OS Validators.
Computes weighted QualityReport and sets quality_audit_passed flag.
"""

from typing import Any

from ape.pipeline.contracts import (
    BasePipelineContext,
    PipelineStage,
    StageResult,
    StageStatus,
)
from ape.quality.contracts import (
    QualityReport,
    ValidationContext,
    ValidationResult,
    ValidationStatus,
    Validator,
)


class QualityAssuranceStage(PipelineStage):
    """
    Constitutional Stage: Quality Assurance (Quality OS).
    Positioned between VerificationStage and ExecutionEvidenceStage.
    """

    def __init__(self, validators: list[Validator] | None = None) -> None:
        if validators is not None:
            self._validators = validators
        else:
            from ape.quality.registry import default_registry
            self._validators = default_registry.discover("python")

    @property
    def name(self) -> str:
        return "quality_assurance"

    def execute(
        self,
        context: BasePipelineContext,
        previous_results: list[StageResult] | None = None,
    ) -> StageResult:
        from pathlib import Path
        topic_slug = getattr(context, "topic_slug", "unknown")
        project_root = getattr(context, "root", getattr(context, "project_root", Path.cwd()))

        deliverables: list[str] = []
        if previous_results:
            for prev in previous_results:
                if prev.stage_name == "task_execution":
                    summary = prev.output_data.get("execution_summary", {})
                    deliverables.extend(summary.get("deliverables", []))
                elif prev.stage_name == "verification":
                    verified = prev.output_data.get("verified_deliverables", [])
                    if verified:
                        deliverables.extend(verified)

        if not deliverables:
            deliverables = context.metadata.get("deliverables", [])

        quality_profile = getattr(context, "quality_profile", None) or context.metadata.get("quality_profile", "standard") or "standard"

        val_context = ValidationContext(
            project_root=project_root,
            topic_slug=topic_slug,
            deliverables=deliverables,
            dry_run=getattr(context, "dry_run", False),
            quality_profile=quality_profile,
            metadata=getattr(context, "metadata", {}),
        )

        from ape.quality.profiles import get_profile_validators, get_validator_weight
        allowed_validator_names = get_profile_validators(quality_profile)
        active_validators = [v for v in self._validators if getattr(v, "name", "") in allowed_validator_names]

        results: list[ValidationResult] = []
        score_weights: dict[str, float] = {}
        weighted_score_accum = 0.0
        total_weight_accum = 0.0
        active_validator_count = 0
        has_critical_failure = False

        for v in active_validators:
            v_name = getattr(v, "name", "unknown")
            score_weights[v_name] = get_validator_weight(v_name)
            res = v.validate(val_context)
            res.is_critical = getattr(v, "is_critical", True)
            res.weight = getattr(v, "weight", 1.0)
            results.append(res)
            if res.status != ValidationStatus.SKIP:
                weighted_score_accum += res.score * res.weight
                total_weight_accum += res.weight
                active_validator_count += 1
            if res.is_critical and res.status == ValidationStatus.FAIL:
                has_critical_failure = True

        overall_score = (
            (weighted_score_accum / total_weight_accum)
            if total_weight_accum > 0
            else 100.0
        )

        quality_audit_passed = (overall_score >= 80.0) and not has_critical_failure

        report = QualityReport(
            overall_score=overall_score,
            quality_audit_passed=quality_audit_passed,
            results=results,
            quality_profile=quality_profile,
            score_weights=score_weights,
            summary={
                "topic_slug": topic_slug,
                "validators_executed": len(active_validators),
                "active_validators": active_validator_count,
                "has_critical_failure": has_critical_failure,
                "quality_profile": quality_profile,
            },
        )

        output_data: dict[str, Any] = {
            "quality_report": report.to_dict(),
            "overall_score": round(overall_score, 2),
            "quality_audit_passed": quality_audit_passed,
        }

        if hasattr(context, "metadata") and isinstance(context.metadata, dict):
            context.metadata["quality_report"] = report.to_dict()
            context.metadata["quality_audit_passed"] = quality_audit_passed

        if not quality_audit_passed:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error=(
                    f"Quality OS Audit FAILED for '{topic_slug}': "
                    f"overall_score={overall_score:.1f}/100.0, "
                    f"critical_failure={has_critical_failure}"
                ),
                output_data=output_data,
            )

        return StageResult(
            stage_name=self.name,
            status=StageStatus.SUCCESS,
            output_data=output_data,
        )
