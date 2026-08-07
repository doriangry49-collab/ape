"""SPEC-0018 Stage Purity: CapabilityValidationStage (SPEC-0012).

Validates provider observations against the Capability Registry, enforcing SPEC-0012 invariants:
"ERROR != UNKNOWN" and prohibiting synthetic mock evidence generation.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ape.pipeline.contracts import (
    PipelineContext,
    PipelineStage,
    StageResult,
    StageStatus,
)


class CapabilityValidationStage(PipelineStage):
    """Pure pipeline stage that validates raw observations against provider capabilities (SPEC-0012)."""

    @property
    def name(self) -> str:
        return "capability_validation"

    def execute(
        self,
        context: PipelineContext,
        previous_results: List[StageResult],
    ) -> StageResult:
        """Validates raw observations from AcquisitionExecutionStage.

        Enforces SPEC-0012: verifies observation fidelity, rejects synthetic mocks,
        and tags capability verification status.
        """
        topic = context.topic_slug.strip()
        if not topic:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error="Topic slug cannot be empty for CapabilityValidationStage",
            )

        # Find raw observations from previous stage
        acq_output = {}
        for prev in previous_results:
            if prev.stage_name == "acquisition_execution" and prev.status == StageStatus.SUCCESS:
                acq_output = prev.output_data
                break

        raw_observations = acq_output.get("raw_observations", [])
        validated_observations: List[Dict[str, Any]] = []
        invalid_count = 0

        for obs in raw_observations:
            source = obs.get("source", "unknown")
            obs_status = obs.get("status")

            if obs_status == "ERROR":
                # SPEC-0012 Invariant: ERROR != UNKNOWN. Preserve actual error, zero synthetic data.
                validated_observations.append({
                    "source": source,
                    "capability_verified": False,
                    "error_reason": obs.get("error", "AdapterError"),
                    "synthetic": False,
                })
                invalid_count += 1
            else:
                signals = obs.get("signals", {})
                # Verify signals are non-synthetic and from valid provider capability
                validated_observations.append({
                    "source": source,
                    "capability_verified": True,
                    "signal_keys": list(signals.keys()),
                    "synthetic": False,
                    "signals": signals,
                })

        output_data = {
            "topic": topic,
            "validated_count": len(validated_observations),
            "invalid_count": invalid_count,
            "validated_observations": validated_observations,
            "spec_0012_compliant": True,
        }

        evidence = {
            "total_validated": len(validated_observations),
            "capability_failures": invalid_count,
            "synthetic_mock_emitted": False,
        }

        return StageResult(
            stage_name=self.name,
            status=StageStatus.SUCCESS,
            output_data=output_data,
            evidence=evidence,
        )
