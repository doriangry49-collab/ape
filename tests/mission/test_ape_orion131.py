"""
ORION-131 — Evidence Contract Binding Proof

Proves:
1. Real research run (HackerNews + AudienceHeuristics) produces structured `business_evidence` items in EvidenceFusionStage.
2. `ResearchPersistStage` persists `business_evidence` into `.build/research/<slug>.json`.
3. Each `business_evidence` item has valid `EvidenceProvenance` (source_adapter, raw_observation, reference_url, etc.).
4. `DecisionEngine.run_decision()` detects `has_business_data == True` and passes items to `InferenceBridge`.
5. `InferenceBridge` aggregates observations into `BridgeResult` with non-empty `provenance_chain` and `evidence_flags`.
6. Full Research → Evidence Fusion → BusinessEvidence → InferenceBridge → DecisionEngine chain operates end-to-end.
"""

from __future__ import annotations

import json
from pathlib import Path

from ape.intelligence.decision.engine import DecisionEngine
from ape.intelligence.research.engine import ResearchEngine
from ape.pipeline.contracts import PipelineContext
from ape.pipeline.runner import ConstitutionalPipelineRunner
from ape.pipeline.stages.acquisition_execution import AcquisitionExecutionStage
from ape.pipeline.stages.capability_validation import CapabilityValidationStage
from ape.pipeline.stages.evidence_fusion import EvidenceFusionStage
from ape.pipeline.stages.explainability import ExplainabilityStage
from ape.pipeline.stages.research_persist import ResearchPersistStage
from ape.pipeline.stages.research_plan import ResearchPlanStage
from ape.pipeline.stages.source_selection import SourceSelectionStage
from ape.project import Project


TOPIC = "ollama_local_llm_ecosystem"
TOPIC_SLUG = "ollama_local_llm_ecosystem"


class TestORION131_EvidenceContractBinding:
    """ORION-131 evidence binding & bridge population proof tests."""

    def test_evidence_fusion_stage_produces_business_evidence(self, tmp_path: Path) -> None:
        """
        Proof 1: EvidenceFusionStage converts validated observations into structured business_evidence dicts.
        """
        ctx = PipelineContext(topic_slug=TOPIC_SLUG, run_id="orion131_fusion_test")
        runner = ConstitutionalPipelineRunner([
            ResearchPlanStage(),
            SourceSelectionStage(),
            AcquisitionExecutionStage(offline=False),
            CapabilityValidationStage(),
            EvidenceFusionStage(),
            ExplainabilityStage(),
            ResearchPersistStage(project_root=tmp_path),
        ])

        results = runner.run(ctx)
        stage_map = {r.stage_name: r for r in results}

        fusion_res = stage_map.get("evidence_fusion")
        assert fusion_res is not None, "EvidenceFusionStage result missing"
        assert fusion_res.status.value == "SUCCESS", f"EvidenceFusionStage failed: {fusion_res.error}"

        fusion_data = fusion_res.output_data or {}
        business_evidence = fusion_data.get("business_evidence", [])

        assert len(business_evidence) > 0, "Proof 1 FAIL: business_evidence list is empty in fusion output"

        # Check provenance fields on each evidence item
        sources_found = set()
        for ev in business_evidence:
            assert "search_intent_observation" in ev, "Missing search_intent_observation"
            assert "pain_observation" in ev, "Missing pain_observation"
            assert "provenance" in ev, "Missing provenance in evidence item"

            prov = ev["provenance"]
            assert "source_adapter" in prov, "Missing source_adapter in provenance"
            assert "raw_observation" in prov, "Missing raw_observation in provenance"
            sources_found.add(prov["source_adapter"])

        assert "HackerNews" in sources_found, f"Proof 1 FAIL: HackerNews missing from provenance sources: {sources_found}"
        assert "AudienceHeuristics" in sources_found, f"Proof 1 FAIL: AudienceHeuristics missing from sources: {sources_found}"

        print(f"\n[Proof 1] Evidence items count: {len(business_evidence)}")
        print(f"[Proof 1] Provenance sources: {sources_found}")

    def test_research_persist_stage_persists_business_evidence(self, tmp_path: Path) -> None:
        """
        Proof 2: ResearchPersistStage writes business_evidence to .build/research/<slug>.json.
        """
        project = Project(root=tmp_path, config_path=tmp_path / ".ape" / "config.toml")
        engine = ResearchEngine(project=project, offline=False)

        report = engine.run_research(TOPIC)
        research_file = tmp_path / ".build" / "research" / f"{TOPIC_SLUG}.json"

        assert research_file.exists(), f"Proof 2 FAIL: Research JSON missing at {research_file}"

        data = json.loads(research_file.read_text(encoding="utf-8"))
        assert "business_evidence" in data, "Proof 2 FAIL: 'business_evidence' key missing from research JSON"

        be_list = data["business_evidence"]
        assert len(be_list) > 0, "Proof 2 FAIL: business_evidence list in JSON is empty"
        assert be_list[0]["provenance"]["source_adapter"] in ("HackerNews", "AudienceHeuristics")

        print(f"\n[Proof 2] Research JSON business_evidence count: {len(be_list)}")
        print(f"[Proof 2] First item provenance: {be_list[0]['provenance']}")

    def test_decision_engine_consumes_business_evidence_and_populates_bridge(self, tmp_path: Path) -> None:
        """
        Proof 3: DecisionEngine reads research JSON, sees has_business_data==True,
        passes items to InferenceBridge, and populates provenance_chain & evidence_flags.
        """
        project = Project(root=tmp_path, config_path=tmp_path / ".ape" / "config.toml")
        ResearchEngine(project=project, offline=False).run_research(TOPIC)

        decision_engine = DecisionEngine(project_root=tmp_path)
        dec_report = decision_engine.run_decision(TOPIC, TOPIC_SLUG)

        assert dec_report.decision_id is not None, "Proof 3 FAIL: decision_id missing"
        assert dec_report.provenance_chain is not None, "Proof 3 FAIL: provenance_chain is None"
        assert len(dec_report.provenance_chain) > 0, "Proof 3 FAIL: provenance_chain is empty"

        # Check evidence flags populated by InferenceBridge
        flags = dec_report.evidence_flags
        assert "payment_signal" in flags, "Proof 3 FAIL: payment_signal missing from evidence_flags"
        assert "identifiable_customer" in flags, "Proof 3 FAIL: identifiable_customer missing from evidence_flags"
        assert "ai_solvability" in flags, "Proof 3 FAIL: ai_solvability missing from evidence_flags"

        # At least identifiable_customer should be True (since discussions/audience were found)
        assert flags["identifiable_customer"] is True, f"Proof 3 FAIL: identifiable_customer flag is {flags['identifiable_customer']}"

        # Verify provenance chain carries actual sources
        adapters = [p.source_adapter for p in dec_report.provenance_chain]
        assert "HackerNews" in adapters or "AudienceHeuristics" in adapters, (
            f"Proof 3 FAIL: Provenance chain adapters unexpected: {adapters}"
        )

        print(f"\n[Proof 3] Decision: {dec_report.decision} (score={dec_report.overall_score})")
        print(f"[Proof 3] Evidence flags: {flags}")
        print(f"[Proof 3] Provenance chain adapters: {adapters}")
        print(f"[Proof 3] Reference URLs: {dec_report.reference_urls}")

    def test_full_evidence_to_decision_lineage(self, tmp_path: Path) -> None:
        """
        Proof 4: Full Research → EvidenceFusion → BusinessEvidence → InferenceBridge → DecisionReport lineage.
        Verifies evidence_hash, decision_id, and decision report persistence.
        """
        project = Project(root=tmp_path, config_path=tmp_path / ".ape" / "config.toml")
        res_report = ResearchEngine(project=project, offline=False).run_research(TOPIC)

        decision_engine = DecisionEngine(project_root=tmp_path)
        dec_report = decision_engine.run_decision(TOPIC, TOPIC_SLUG)

        # Decision artifact must exist
        dec_file = tmp_path / ".build" / "decisions" / f"{TOPIC_SLUG}.json"
        assert dec_file.exists(), f"Proof 4 FAIL: Decision artifact missing at {dec_file}"

        dec_data = json.loads(dec_file.read_text(encoding="utf-8"))

        assert dec_data.get("decision_id") == dec_report.decision_id
        assert dec_data.get("evidence_hash") == dec_report.evidence_hash
        assert dec_data.get("evidence_flags") == dec_report.evidence_flags

        # Governance log
        gov_dir = tmp_path / ".governance" / "evidence"
        dec_logs = list(gov_dir.glob("decisions-*.jsonl")) if gov_dir.exists() else []
        assert len(dec_logs) > 0, "Proof 4 FAIL: Decision evidence log not written to .governance/evidence/"

        print(f"\n[Proof 4] Lineage verified. Decision file: {dec_file.name}")
        print(f"[Proof 4] Evidence hash: {dec_report.evidence_hash[:16]}...")
        print(f"[Proof 4] Governance evidence log: {dec_logs[0].name}")
