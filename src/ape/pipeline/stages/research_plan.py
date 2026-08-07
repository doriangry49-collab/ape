"""SPEC-0018 Stage Purity: ResearchPlanStage.

Formulates research plan and search strategy for a target topic, producing a pure StageResult.
"""

from __future__ import annotations

import re
from typing import List

from ape.pipeline.contracts import (
    PipelineContext,
    PipelineStage,
    StageResult,
    StageStatus,
)


class ResearchPlanStage(PipelineStage):
    """Pure pipeline stage that formulates the research plan and search query strategy."""

    @property
    def name(self) -> str:
        return "research_plan"

    def execute(
        self,
        context: PipelineContext,
        previous_results: List[StageResult],
    ) -> StageResult:
        """Executes pure research plan formulation without side effects.

        Reads topic from context, normalizes topic slug/ID, and formulates search strategy.
        """
        topic = context.topic_slug.strip()
        if not topic:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error="Topic slug cannot be empty for ResearchPlanStage",
            )

        clean_topic_id = re.sub(r"[^a-z0-9]", "", topic.lower())[:8]
        if not clean_topic_id:
            clean_topic_id = "default"

        plan_data = {
            "topic": topic,
            "clean_topic_id": clean_topic_id,
            "search_queries": [
                topic,
                f"{topic} problem pain points",
                f"{topic} competitors alternative",
            ],
            "target_providers": ["HackerNews", "AudienceHeuristics"],
        }

        evidence = {
            "query_count": len(plan_data["search_queries"]),
            "target_providers": plan_data["target_providers"],
        }

        return StageResult(
            stage_name=self.name,
            status=StageStatus.SUCCESS,
            output_data=plan_data,
            evidence=evidence,
        )
