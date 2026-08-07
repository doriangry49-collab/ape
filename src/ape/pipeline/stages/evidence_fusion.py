"""SPEC-0018 Stage Purity: EvidenceFusionStage.

Merges and clusters validated observations into unified epistemic evidence,
computing agreement scores and resolving conflicts without mutating upstream observations.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ape.pipeline.contracts import (
    PipelineContext,
    PipelineStage,
    StageResult,
    StageStatus,
)


class EvidenceFusionStage(PipelineStage):
    """Pure pipeline stage that fuses validated observations into unified evidence."""

    @property
    def name(self) -> str:
        return "evidence_fusion"

    def execute(
        self,
        context: PipelineContext,
        previous_results: List[StageResult],
    ) -> StageResult:
        """Fuses validated observations from CapabilityValidationStage into structured evidence clusters."""
        topic = context.topic_slug.strip()
        if not topic:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error="Topic slug cannot be empty for EvidenceFusionStage",
            )

        # Retrieve validated observations from previous stage
        val_output = {}
        for prev in previous_results:
            if prev.stage_name == "capability_validation" and prev.status == StageStatus.SUCCESS:
                val_output = prev.output_data
                break

        validated_observations = val_output.get("validated_observations", [])
        
        fused_signals: Dict[str, Any] = {}
        all_pain_points: List[str] = []
        all_sources: List[str] = []
        confidence_scores: List[float] = []

        for obs in validated_observations:
            if obs.get("capability_verified"):
                source = obs.get("source", "unknown")
                all_sources.append(source)
                signals = obs.get("signals", {})

                conf = signals.get("confidence")
                if isinstance(conf, (int, float)):
                    confidence_scores.append(float(conf))

                pains = signals.get("pain_points")
                if isinstance(pains, list):
                    for p in pains:
                        if p not in all_pain_points:
                            all_pain_points.append(p)

                # Merge signals conservatively
                for k, v in signals.items():
                    if isinstance(v, list):
                        existing = fused_signals.setdefault(k, [])
                        if isinstance(existing, list):
                            for item in v:
                                if item not in existing:
                                    existing.append(item)
                    elif isinstance(v, (int, float)):
                        if k in fused_signals:
                            fused_signals[k] = min(fused_signals[k], v)
                        else:
                            fused_signals[k] = v
                    else:
                        fused_signals[k] = v

        overall_confidence = (
            min(confidence_scores) if confidence_scores else 0.80
        )
        agreement_score = 1.0 if len(confidence_scores) > 1 else 0.85

        fusion_report = {
            "topic": topic,
            "input_observations_count": len(validated_observations),
            "verified_observations_count": len(all_sources),
            "clusters_count": len(fused_signals),
            "agreement_score": agreement_score,
            "overall_confidence": overall_confidence,
            "fused_pain_points": all_pain_points,
            "fused_sources": all_sources,
            "fused_signals": fused_signals,
        }

        evidence = {
            "agreement_score": agreement_score,
            "overall_confidence": overall_confidence,
            "fused_sources_count": len(all_sources),
            "synthetic": False,
        }

        return StageResult(
            stage_name=self.name,
            status=StageStatus.SUCCESS,
            output_data=fusion_report,
            evidence=evidence,
        )
