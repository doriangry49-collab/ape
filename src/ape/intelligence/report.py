from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from ape import __version__
from ape.intelligence.decision.engine import DecisionEngine
from ape.intelligence.research.engine import ResearchEngine
from ape.project import Project
from ape.utils import append_to_evidence, slugify


class MarketReportFormatter:
    """Compiles and formats an Executive Market Briefing report combining Research & Decision signals."""

    def __init__(self, project: Project, offline: bool = False) -> None:
        self._project = project
        self._offline = offline
        self._research_engine = ResearchEngine(project, offline=offline)
        self._decision_engine = DecisionEngine(project.root)

    def generate_report(self, topic: str) -> dict[str, Any]:
        """Runs research & decision pipeline and compiles Executive Brief artifacts."""
        topic_slug = slugify(topic)
        
        # 1. Gather research signals
        research_report = self._research_engine.run_research(topic)

        # 2. Run decision engine evaluation
        decision_report = self._decision_engine.run_decision(topic, topic_slug)

        now_utc = datetime.now(UTC)

        # 3. Assemble structured Executive Market Brief data
        report_data: dict[str, Any] = {
            "metadata": {
                "schema_version": "1.0",
                "created_at": now_utc.isoformat(),
                "ape_version": __version__,
                "topic": topic,
                "topic_slug": topic_slug,
            },
            "executive_summary": {
                "topic": topic,
                "decision": decision_report.decision,
                "policy": decision_report.policy,
                "overall_score": decision_report.overall_score,
                "confidence": decision_report.confidence,
                "next_recommended_step": decision_report.next_step,
            },
            "market_intelligence": {
                "target_audience": research_report.target_audience,
                "competitors": research_report.competitors,
                "pain_points": research_report.pain_points,
                "market_signals": research_report.market_signals,
                "risks": research_report.risks,
                "sources": research_report.sources,
                "suggested_mvp": research_report.suggested_mvp,
            },
            "decision_rationale": decision_report.rationale,
            "evidence_lineage": {
                "decision_id": decision_report.decision_id,
                "evidence_hash": decision_report.evidence_hash,
                "ledger_file": f".governance/evidence/decisions-{now_utc.strftime('%Y-%m')}.jsonl",
            },
        }

        # 4. Save artifacts
        self._save_artifacts(topic_slug, report_data)

        return report_data

    def _save_artifacts(self, topic_slug: str, data: dict[str, Any]) -> None:
        """Write JSON and Markdown artifacts under .build/reports/."""
        reports_dir = self._project.root / ".build" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # 1. JSON Report
        json_file = reports_dir / f"{topic_slug}-market-brief.json"
        json_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # 2. Append to governance evidence ledger
        evidence_dir = self._project.root / ".governance" / "evidence"
        append_to_evidence(evidence_dir, "market_reports", data)

        # 3. Formatted Executive Markdown Brief
        exec_sum = data["executive_summary"]
        mkt_intel = data["market_intelligence"]
        lineage = data["evidence_lineage"]

        md_content = (
            f"# APE Executive Market Brief: {data['metadata']['topic']}\n\n"
            f"**Generated:** {data['metadata']['created_at']} UTC  \n"
            f"**Decision:** {exec_sum['decision']}  \n"
            f"**Policy Gate:** {exec_sum['policy']}  \n"
            f"**Opportunity Score:** {exec_sum['overall_score']}/100  \n"
            f"**Confidence:** {exec_sum['confidence']}%  \n"
            f"**Next Step:** {exec_sum['next_recommended_step']}\n\n"
            "---\n\n"
            "## 1. Executive Summary\n"
            f"APE evaluated real-world market signals for **{data['metadata']['topic']}** and calculated an overall "
            f"opportunity score of **{exec_sum['overall_score']}/100** with **{exec_sum['confidence']}%** confidence.\n\n"
            "## 2. Customer Pain Points\n"
            + "\n".join(f"- {p}" for p in mkt_intel["pain_points"]) + "\n\n"
            "## 3. Market Signals & Discussions\n"
            + "\n".join(f"- {s}" for s in mkt_intel["market_signals"]) + "\n\n"
            "## 4. Target Audience & Competitors\n"
            "**Audience:**\n" + "\n".join(f"- {a}" for a in mkt_intel["target_audience"]) + "\n\n"
            "**Competitors:**\n" + "\n".join(f"- {c}" for c in mkt_intel["competitors"]) + "\n\n"
            "## 5. Decision Rationale & Policy Boundary\n"
            + "\n".join(f"- {r}" for r in data["decision_rationale"]) + "\n\n"
            "## 6. Suggested MVP Scope\n"
            + "\n".join(f"- {m}" for m in mkt_intel["suggested_mvp"]) + "\n\n"
            "## 7. Audit Evidence & Lineage\n"
            f"- **Decision ID:** `{lineage['decision_id']}`  \n"
            f"- **Evidence SHA-256 Hash:** `{lineage['evidence_hash']}`  \n"
            f"- **Ledger Path:** `{lineage['ledger_file']}`  \n"
        )

        md_file = reports_dir / f"{topic_slug}-market-brief.md"
        md_file.write_text(md_content, encoding="utf-8")
