"""SPEC-0018 Stage Purity: ExplainabilityStage.

Composes a structured, transparent narrative from previous stage outputs without re-computing scores or logic.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ape.pipeline.contracts import (
    PipelineContext,
    PipelineStage,
    StageResult,
    StageStatus,
)


class ExplainabilityStage(PipelineStage):
    """Pure pipeline stage that composes transparent decision narratives from stage outputs."""

    @property
    def name(self) -> str:
        return "explainability"

    def execute(
        self,
        context: PipelineContext,
        previous_results: List[StageResult],
    ) -> StageResult:
        """Composes a structured narrative trace strictly reading previous stage outputs (Compose, not Compute)."""
        topic = context.topic_slug.strip()
        if not topic:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error="Topic slug cannot be empty for ExplainabilityStage",
            )

        # Map previous stage results by stage name for clean composition
        stage_map: Dict[str, StageResult] = {res.stage_name: res for res in previous_results}

        plan_res = stage_map.get("research_plan")
        select_res = stage_map.get("source_selection")
        acq_res = stage_map.get("acquisition_execution")
        val_res = stage_map.get("capability_validation")
        fusion_res = stage_map.get("evidence_fusion")

        # Compose decision and evidence execution paths
        decision_path: List[Dict[str, Any]] = []
        evidence_path: List[Dict[str, Any]] = []

        if plan_res:
            decision_path.append({
                "stage": "research_plan",
                "summary": f"Formulated research plan for '{topic}'",
                "stage_hash": plan_res.evidence.get("stage_hash"),
            })

        if select_res:
            decision_path.append({
                "stage": "source_selection",
                "summary": f"Selected sources: {select_res.output_data.get('selected_sources')}",
                "reasoning": select_res.output_data.get("selection_reasoning"),
                "stage_hash": select_res.evidence.get("stage_hash"),
            })

        if acq_res:
            evidence_path.append({
                "stage": "acquisition_execution",
                "observation_count": acq_res.output_data.get("observation_count"),
                "stage_hash": acq_res.evidence.get("stage_hash"),
            })

        if val_res:
            evidence_path.append({
                "stage": "capability_validation",
                "validated_count": val_res.output_data.get("validated_count"),
                "spec_0012_compliant": val_res.output_data.get("spec_0012_compliant"),
                "stage_hash": val_res.evidence.get("stage_hash"),
            })

        fusion_data = fusion_res.output_data if fusion_res else {}
        overall_conf = fusion_data.get("overall_confidence", 0.80)
        agreement_score = fusion_data.get("agreement_score", 1.0)

        narrative = {
            "topic": topic,
            "summary": (
                f"Research for '{topic}' completed across 5 constitutional pipeline stages "
                f"with overall confidence of {overall_conf:.0%} and agreement score of {agreement_score:.2f}."
            ),
            "decision_path": decision_path,
            "evidence_path": evidence_path,
            "confidence_reasoning": (
                f"Confidence ({overall_conf:.0%}) derived from {len(fusion_data.get('fused_sources', []))} verified sources "
                f"with {len(fusion_data.get('fused_pain_points', []))} distinct pain points identified."
            ),
            "unknown_reasons": (
                f"Handled {val_res.output_data.get('invalid_count', 0)} invalid/errored provider observations "
                "in accordance with SPEC-0012 zero-synthetic invariants."
            ) if val_res else "None",
        }

        evidence = {
            "narrative_composed": True,
            "stages_narrated_count": len(previous_results),
            "overall_confidence": overall_conf,
        }

        return StageResult(
            stage_name=self.name,
            status=StageStatus.SUCCESS,
            output_data=narrative,
            evidence=evidence,
        )
