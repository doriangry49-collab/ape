"""SPEC-0018 Stage Purity: ResearchPersistStage.

Handles immutable evidence persistence (.governance/evidence/) and canonical state updates (.build/research/).
"""

from __future__ import annotations

import json
import re
from typing import List

from ape.pipeline.contracts import (
    PipelineContext,
    PipelineStage,
    StageResult,
    StageStatus,
)
from ape.utils import append_to_evidence


class ResearchPersistStage(PipelineStage):
    """Pure pipeline stage that handles report creation and dual-write artifact persistence."""

    def __init__(self, project_root: Any) -> None:
        self._project_root = project_root

    @property
    def name(self) -> str:
        return "research_persist"

    def execute(
        self,
        context: PipelineContext,
        previous_results: List[StageResult],
    ) -> StageResult:
        """Persists research report to .build/research/ and append-only evidence history."""
        topic = context.topic_slug.strip()
        if not topic:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                error="Topic slug cannot be empty for ResearchPersistStage",
            )

        # Map previous stage results
        stage_map: Dict[str, StageResult] = {res.stage_name: res for res in previous_results}

        fusion_res = stage_map.get("evidence_fusion")
        fusion_data = fusion_res.output_data if fusion_res else {}
        explain_res = stage_map.get("explainability")
        explain_data = explain_res.output_data if explain_res else {}

        # Prepare directory paths
        build_dir = self._project_root / ".build" / "research"
        build_dir.mkdir(parents=True, exist_ok=True)
        evidence_dir = self._project_root / ".governance" / "evidence"

        slug = re.sub(r"[^a-z0-9_]", "", topic.lower().replace(" ", "_"))
        if not slug:
            slug = "unnamed_topic"

        json_data = {
            "metadata": {
                "schema_version": "1.0",
                "topic": topic,
                "run_id": context.run_id,
                "pipeline_stage_hash": explain_res.evidence.get("stage_hash") if explain_res else None,
                "explainability_summary": explain_data.get("summary"),
            },
            "topic": topic,
            "next_recommended_action": "BUILD" if fusion_data.get("overall_confidence", 0.8) >= 0.8 else "VALIDATE",
            "confidence": fusion_data.get("overall_confidence", 0.80),
            "sources": fusion_data.get("fused_sources", []),
            "pain_points": fusion_data.get("fused_pain_points", []),
            "fused_signals": fusion_data.get("fused_signals", {}),
        }

        # 1. Canonical State JSON
        json_file = build_dir / f"{slug}.json"
        json_file.write_text(json.dumps(json_data, indent=2), encoding="utf-8")

        # 2. Immutable Evidence Log
        append_to_evidence(evidence_dir, "research", json_data)

        # 3. Canonical State Markdown
        md_file = build_dir / f"{slug}.md"
        md_content = (
            f"# Research Report: {topic}\n\n"
            f"**Run ID:** {context.run_id}  \n"
            f"**Next Recommended Action:** {json_data['next_recommended_action']}  \n"
            f"**Confidence Score:** {json_data['confidence']:.0%}  \n"
            f"**Sources:** {', '.join(json_data['sources'])}\n\n"
            "## Pain Points\n"
            + "\n".join(f"- {p}" for p in json_data["pain_points"]) + "\n\n"
            "## Explainability Summary\n"
            f"{explain_data.get('summary', 'N/A')}\n"
        )
        md_file.write_text(md_content, encoding="utf-8")

        output_data = {
            "topic": topic,
            "slug": slug,
            "json_path": str(json_file),
            "md_path": str(md_file),
            "persisted": True,
        }

        evidence = {
            "json_artifact": f"{slug}.json",
            "md_artifact": f"{slug}.md",
            "evidence_logged": True,
        }

        return StageResult(
            stage_name=self.name,
            status=StageStatus.SUCCESS,
            output_data=output_data,
            evidence=evidence,
        )
