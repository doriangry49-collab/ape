"""
ORION-132 — Multi-Source Research Provider & Evidence Proof

Proves:
1. GitHubTrendingResearchProvider conforms to BaseResearchProvider, fetching live GitHub repo signals & offline mock fallback.
2. Source isolation: HackerNews only, GitHub Trending only, and Multi-source acquisition operate independently.
3. Multi-source evidence fusion: EvidenceFusionStage merges HackerNews, GitHubTrending, and AudienceHeuristics signals.
4. BusinessEvidence items carry source-specific EvidenceProvenance (source_adapter="GitHubTrending", reference_url="https://github.com/...").
5. ResearchPersistStage persists multi-source research report & business_evidence to .build/research/<slug>.json.
6. DecisionEngine consumes multi-source research artifact, populating InferenceBridge provenance_chain with all active sources.
"""

from __future__ import annotations

import json
from pathlib import Path

from ape.intelligence.decision.engine import DecisionEngine
from ape.intelligence.research.engine import ResearchEngine
from ape.intelligence.research.providers.github_trending import GitHubTrendingResearchProvider
from ape.pipeline.contracts import PipelineContext, StageStatus
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


class TestORION132_MultiSourceResearchProof:
    """ORION-132 Multi-source provider acquisition & evidence fusion proof tests."""

    # ------------------------------------------------------------------
    # 1. GitHub Trending Provider direct acquisition
    # ------------------------------------------------------------------

    def test_github_trending_provider_live_acquisition(self) -> None:
        """
        Proof 1: GitHubTrendingResearchProvider fetches live repository signals from GitHub API.
        """
        provider = GitHubTrendingResearchProvider(offline=False)
        signals = provider.fetch_signals(TOPIC)

        assert "discussions" in signals, "Missing discussions in GitHub signals"
        assert "pain_points" in signals, "Missing pain_points in GitHub signals"
        assert "market_signals" in signals, "Missing market_signals in GitHub signals"
        assert "competitors" in signals, "Missing competitors in GitHub signals"
        assert signals.get("sources") == ["GitHubTrending"], f"Unexpected sources: {signals.get('sources')}"

        discussions = signals["discussions"]
        assert len(discussions) > 0, "Proof 1 FAIL: Live GitHub API returned zero repositories"

        top_repo = discussions[0]
        assert "url" in top_repo and "github.com" in top_repo["url"], f"Invalid repo URL: {top_repo.get('url')}"
        assert top_repo.get("points", 0) > 0, f"Expected stargazers count > 0, got {top_repo.get('points')}"

        print(f"\n[Proof 1] GitHub live repos count: {len(discussions)}")
        print(f"[Proof 1] Top repo: {top_repo['title']} ({top_repo['url']})")
        print(f"[Proof 1] Market signals: {signals['market_signals']}")

    def test_github_trending_provider_offline_acquisition(self) -> None:
        """
        Proof 1b: GitHubTrendingResearchProvider offline mock fallback works deterministically.
        """
        provider = GitHubTrendingResearchProvider(offline=True)
        signals = provider.fetch_signals(TOPIC)

        assert len(signals["discussions"]) == 2
        assert signals["sources"] == ["GitHubTrending"]
        assert "github.com" in signals["discussions"][0]["url"]

        print(f"\n[Proof 1b] Offline GitHub mock repos: {len(signals['discussions'])}")

    # ------------------------------------------------------------------
    # 2. Source Isolation Tests
    # ------------------------------------------------------------------

    def test_source_isolation_individual_providers(self) -> None:
        """
        Proof 2: Source isolation test — each provider operates independently without cross-provider side effects.
        A) HackerNews only
        B) GitHub Trending only
        C) AudienceHeuristics only
        """
        from ape.intelligence.research.providers.audience import HeuristicAudienceProvider
        from ape.intelligence.research.providers.hackernews import HackerNewsResearchProvider

        hn_prov = HackerNewsResearchProvider(offline=False)
        gh_prov = GitHubTrendingResearchProvider(offline=False)
        aud_prov = HeuristicAudienceProvider()

        hn_sig = hn_prov.fetch_signals(TOPIC)
        gh_sig = gh_prov.fetch_signals(TOPIC)
        aud_sig = aud_prov.fetch_signals(TOPIC)

        assert hn_sig["sources"] == ["HackerNews"]
        assert gh_sig["sources"] == ["GitHubTrending"]
        assert aud_sig["sources"] == ["AudienceHeuristics"]

        assert len(hn_sig["discussions"]) > 0
        assert len(gh_sig["discussions"]) > 0
        assert len(aud_sig["target_audience"]) > 0

        print(f"\n[Proof 2] Isolation A (HN): {len(hn_sig['discussions'])} discussions")
        print(f"[Proof 2] Isolation B (GitHub): {len(gh_sig['discussions'])} repos")
        print(f"[Proof 2] Isolation C (Audience): {len(aud_sig['target_audience'])} target segments")

    # ------------------------------------------------------------------
    # 3. Multi-Source Pipeline & Fusion Evidence
    # ------------------------------------------------------------------

    def test_multi_source_evidence_fusion(self, tmp_path: Path) -> None:
        """
        Proof 3: EvidenceFusionStage merges observations from HackerNews, GitHubTrending, and AudienceHeuristics.
        Verifies business_evidence list contains items from all 3 sources with correct provenance.
        """
        ctx = PipelineContext(topic_slug=TOPIC_SLUG, run_id="orion132_multisource_test")
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
        assert fusion_res is not None and fusion_res.status == StageStatus.SUCCESS, (
            f"EvidenceFusionStage failed: {fusion_res.error if fusion_res else 'missing'}"
        )

        fusion_data = fusion_res.output_data or {}
        fused_sources = fusion_data.get("fused_sources", [])
        business_evidence = fusion_data.get("business_evidence", [])

        assert "HackerNews" in fused_sources, f"Missing HackerNews: {fused_sources}"
        assert "GitHubTrending" in fused_sources, f"Missing GitHubTrending: {fused_sources}"
        assert "AudienceHeuristics" in fused_sources, f"Missing AudienceHeuristics: {fused_sources}"

        sources_in_be = [ev["provenance"]["source_adapter"] for ev in business_evidence]
        assert "HackerNews" in sources_in_be, f"Missing HackerNews BE: {sources_in_be}"
        assert "GitHubTrending" in sources_in_be, f"Missing GitHubTrending BE: {sources_in_be}"
        assert "AudienceHeuristics" in sources_in_be, f"Missing AudienceHeuristics BE: {sources_in_be}"

        # Find GitHub evidence item and check reference_url
        gh_be = next(ev for ev in business_evidence if ev["provenance"]["source_adapter"] == "GitHubTrending")
        assert gh_be["provenance"]["reference_url"] is not None, "GitHub evidence item missing reference_url"
        assert "github.com" in gh_be["provenance"]["reference_url"], f"Invalid GitHub reference_url: {gh_be['provenance']['reference_url']}"

        print(f"\n[Proof 3] Fused sources count: {len(fused_sources)} -> {fused_sources}")
        print(f"[Proof 3] BusinessEvidence count: {len(business_evidence)}")
        print(f"[Proof 3] GitHub item reference URL: {gh_be['provenance']['reference_url']}")

    # ------------------------------------------------------------------
    # 4. Multi-Source DecisionEngine & InferenceBridge Integration
    # ------------------------------------------------------------------

    def test_multi_source_decision_engine_provenance(self, tmp_path: Path) -> None:
        """
        Proof 4: DecisionEngine consumes multi-source research artifact.
        InferenceBridge provenance_chain contains HackerNews, GitHubTrending, AudienceHeuristics.
        """
        project = Project(root=tmp_path, config_path=tmp_path / ".ape" / "config.toml")
        res_report = ResearchEngine(project=project, offline=False).run_research(TOPIC)

        decision_engine = DecisionEngine(project_root=tmp_path)
        dec_report = decision_engine.run_decision(TOPIC, TOPIC_SLUG)

        # Check persisted research artifact
        research_file = tmp_path / ".build" / "research" / f"{TOPIC_SLUG}.json"
        assert research_file.exists()
        res_data = json.loads(research_file.read_text(encoding="utf-8"))
        assert "GitHubTrending" in res_data.get("sources", [])

        # Check DecisionReport provenance_chain
        adapters = [p.source_adapter for p in dec_report.provenance_chain]
        assert "HackerNews" in adapters, f"Missing HackerNews adapter: {adapters}"
        assert "GitHubTrending" in adapters, f"Missing GitHubTrending adapter: {adapters}"
        assert "AudienceHeuristics" in adapters, f"Missing AudienceHeuristics adapter: {adapters}"

        # Check reference URLs (should contain both news.ycombinator.com or sleepingrobots and github.com)
        urls_str = " ".join(dec_report.reference_urls)
        assert "github.com" in urls_str, f"Missing github.com in reference URLs: {dec_report.reference_urls}"

        print(f"\n[Proof 4] Multi-source Decision: {dec_report.decision} (score={dec_report.overall_score})")
        print(f"[Proof 4] Decision ID: {dec_report.decision_id}")
        print(f"[Proof 4] Provenance adapters: {adapters}")
        print(f"[Proof 4] Reference URLs count: {len(dec_report.reference_urls)}")
