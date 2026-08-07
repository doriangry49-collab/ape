from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime

from ape import __version__
from ape.intelligence.research.models import ResearchReport
from ape.pipeline.contracts import PipelineContext
from ape.pipeline.runner import ConstitutionalPipelineRunner
from ape.pipeline.stages.acquisition_execution import AcquisitionExecutionStage
from ape.pipeline.stages.capability_validation import CapabilityValidationStage
from ape.pipeline.stages.evidence_fusion import EvidenceFusionStage
from ape.pipeline.stages.explainability import ExplainabilityStage
from ape.pipeline.stages.research_plan import ResearchPlanStage
from ape.pipeline.stages.research_persist import ResearchPersistStage
from ape.pipeline.stages.source_selection import SourceSelectionStage
from ape.project import Project


class ResearchEngine:
    """Orchestrates research providers to gather signals and compile reports via Constitutional Pipeline."""

    def __init__(self, project: Project, offline: bool = False) -> None:
        self._project = project
        self._offline = offline

    def run_research(self, topic: str) -> ResearchReport:
        """Fetch signals from all providers, merge into ResearchReport, and save artifacts via 7-stage ResearchPipeline."""
        # --- Strangler Pattern PR-7 Full Pipeline Integration ---
        ctx = PipelineContext(
            topic_slug=topic,
            run_id=f"res_run_{uuid.uuid4().hex[:8]}",
        )
        runner = ConstitutionalPipelineRunner([
            ResearchPlanStage(),
            SourceSelectionStage(),
            AcquisitionExecutionStage(offline=self._offline),
            CapabilityValidationStage(),
            EvidenceFusionStage(),
            ExplainabilityStage(),
            ResearchPersistStage(project_root=self._project.root),
        ])
        pipeline_results = runner.run(ctx)
        plan_result = pipeline_results[0]
        selection_result = pipeline_results[1]
        acq_result = pipeline_results[2]
        val_result = pipeline_results[3]
        fusion_result = pipeline_results[4]
        explain_result = pipeline_results[5]
        persist_result = pipeline_results[6]

        clean_topic_id = plan_result.output_data.get("clean_topic_id", "default")
        acquisition_plan = selection_result.output_data
        validated_data = val_result.output_data
        fusion_data = fusion_result.output_data
        explain_data = explain_result.output_data
        combined_signals = fusion_data.get("fused_signals", {})
        # --------------------------------------------------------

        confidence = fusion_data.get("overall_confidence", 0.80)
        pains_list = fusion_data.get("fused_pain_points", [])
        sources_list = fusion_data.get("fused_sources", ["HackerNews", "AudienceHeuristics"])
        if not isinstance(sources_list, list):
            sources_list = [str(sources_list)]

        # Check for matching discovery scan lineage in .build/scans/
        discovery_lineage = None
        try:
            from ape.intelligence.scanner.persistence import ScanPersistence
            scan_persistence = ScanPersistence(self._project.root)
            matched_opp, scan_meta, json_path = scan_persistence.find_matching_opportunity(topic)

            if matched_opp and scan_meta and json_path:
                discovery_lineage = {
                    "scan_mode": scan_meta.get("mode", "unknown"),
                    "scanned_at": scan_meta.get("scanned_at"),
                    "source_artifact": json_path.name,
                    "opportunity_title": matched_opp.get("title"),
                    "opportunity_slug": matched_opp.get("slug"),
                    "discovery_source": matched_opp.get("source"),
                    "discovery_score": matched_opp.get("score"),
                    "is_hypothesis": matched_opp.get("is_hypothesis", True),
                }
                sources_list.append(f"DiscoveryScan({json_path.name})")

                # Incorporate discovery pain point as seed input signal if present
                pain_info = matched_opp.get("pain_point")
                if isinstance(pain_info, dict) and pain_info.get("description"):
                    seed_pain = f"[Discovery Signal] {pain_info.get('description')}"
                    if seed_pain not in pains_list:
                        pains_list.append(seed_pain)
        except Exception:
            # Gracefully handle any unexpected scanner load errors without halting research
            discovery_lineage = None

        conf_val = float(confidence)
        if conf_val < 0.60:
            action = "IGNORE"
        elif conf_val >= 0.80 and len(pains_list) >= 3:
            action = "BUILD"
        elif conf_val >= 0.75 and len(pains_list) >= 1:
            action = "VALIDATE"
        else:
            action = "WATCH"

        now_utc = datetime.now(UTC)

        metadata = {
            "schema_version": "1.0",
            "created_at": now_utc.isoformat(),
            "ape_version": __version__,
            "research_id": f"res_{uuid.uuid4().hex[:8]}",
            "opportunity_id": f"op_{clean_topic_id}",
            "pipeline_stage_hash": persist_result.evidence.get("stage_hash"),
            "pipeline_parent_hash": persist_result.evidence.get("parent_hash"),
            "acquisition_plan": acquisition_plan,
            "observation_count": acq_result.output_data.get("observation_count", 0),
            "spec_0012_validated": validated_data.get("spec_0012_compliant", False),
            "agreement_score": fusion_data.get("agreement_score", 1.0),
            "explainability_summary": explain_data.get("summary"),
            "decision_path": explain_data.get("decision_path"),
            "evidence_path": explain_data.get("evidence_path"),
            "persisted_artifacts": persist_result.output_data,
        }

        if discovery_lineage:
            metadata["discovery_lineage"] = discovery_lineage

        # Build clean ResearchReport
        return ResearchReport(
            topic=topic,
            target_audience=combined_signals.get("target_audience", []),  # type: ignore
            competitors=combined_signals.get("competitors", []),  # type: ignore
            pain_points=pains_list,  # type: ignore
            market_signals=combined_signals.get("market_signals", []),  # type: ignore
            risks=combined_signals.get("risks", []),  # type: ignore
            confidence=conf_val,  # type: ignore
            sources=sources_list,  # type: ignore
            discussions=combined_signals.get("discussions", []),  # type: ignore
            suggested_mvp=combined_signals.get("suggested_mvp", []),  # type: ignore
            timestamp=now_utc,
            next_recommended_action=action,
            metadata=metadata
        )
