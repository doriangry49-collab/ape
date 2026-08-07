"""SPEC-0018 Stage Purity: SourceSelectionStage.

Formulates an explicit source acquisition plan based on topic requirements and budget constraints,
strictly separating source selection decision from actual execution.
"""

from __future__ import annotations

from typing import List

from ape.pipeline.contracts import (
    PipelineContext,
    PipelineStage,
    StageResult,
    StageStatus,
)


class SourceSelectionStage(PipelineStage):
    """Pure pipeline stage that determines information acquisition targets and strategy."""

    @property
    def name(self) -> str:
        return "source_selection"

    def execute(
        self,
        context: PipelineContext,
        previous_results: List[StageResult],
    ) -> StageResult:
        """Executes source selection decision logic.

        Reads plan from ResearchPlanStage (if present) and outputs an explicit acquisition plan.
        """
        topic = context.topic_slug.strip()
        if not topic:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error="Topic slug cannot be empty for SourceSelectionStage",
            )

        # Inspect previous plan stage output if available
        plan_output = {}
        for prev in previous_results:
            if prev.stage_name == "research_plan" and prev.status == StageStatus.SUCCESS:
                plan_output = prev.output_data
                break

        selected_sources = plan_output.get(
            "target_providers", ["HackerNews", "AudienceHeuristics"]
        )

        acquisition_plan = {
            "topic": topic,
            "selected_sources": selected_sources,
            "priority_source": selected_sources[0] if selected_sources else "HackerNews",
            "estimated_cost": "low",
            "estimated_time_seconds": 10.0,
            "budget_profile": context.resource_budget.get("profile", "default"),
            "selection_reasoning": (
                f"Selected {len(selected_sources)} sources for topic '{topic}' "
                "to capture technical discussions and audience pain points."
            ),
        }

        evidence = {
            "source_count": len(selected_sources),
            "sources": selected_sources,
            "reasoning": acquisition_plan["selection_reasoning"],
        }

        return StageResult(
            stage_name=self.name,
            status=StageStatus.SUCCESS,
            output_data=acquisition_plan,
            evidence=evidence,
        )
