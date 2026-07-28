from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime

from ape import __version__
from ape.intelligence.research.models import ResearchReport
from ape.intelligence.research.providers.audience import HeuristicAudienceProvider
from ape.intelligence.research.providers.hackernews import HackerNewsResearchProvider
from ape.project import Project


class ResearchEngine:
    """Orchestrates research providers to gather signals and compile reports."""

    def __init__(self, project: Project, offline: bool = False) -> None:
        self._project = project
        self._offline = offline
        self._providers = [
            HackerNewsResearchProvider(offline=offline),
            HeuristicAudienceProvider()
        ]

    def run_research(self, topic: str) -> ResearchReport:
        """Fetch signals from all providers, merge into ResearchReport, and save artifacts."""
        combined_signals: dict[str, list | float | str] = {}
        for provider in self._providers:
            signals = provider.fetch_signals(topic)
            for k, v in signals.items():
                if isinstance(v, list):
                    existing = combined_signals.setdefault(k, [])
                    if isinstance(existing, list):
                        existing.extend(v)
                elif isinstance(v, (int, float)):
                    if k in combined_signals:
                        # Take the minimum confidence score for conservative estimate
                        combined_signals[k] = min(combined_signals[k], v)  # type: ignore
                    else:
                        combined_signals[k] = v
                else:
                    combined_signals[k] = v

        # Calculate heuristics for next recommended action
        confidence = combined_signals.get("confidence", 0.80)
        pain_points = combined_signals.get("pain_points", [])
        
        # Ensure we have clean typing
        conf_val = float(confidence) if isinstance(confidence, (int, float)) else 0.80
        pains_list = pain_points if isinstance(pain_points, list) else []

        if conf_val < 0.60:
            action = "IGNORE"
        elif conf_val >= 0.80 and len(pains_list) >= 3:
            action = "BUILD"
        elif conf_val >= 0.75 and len(pains_list) >= 1:
            action = "VALIDATE"
        else:
            action = "WATCH"

        now_utc = datetime.now(UTC)
        clean_topic_id = re.sub(r'[^a-z0-9]', '', topic.lower())[:8]
        if not clean_topic_id:
            clean_topic_id = "default"

        metadata = {
            "schema_version": "1.0",
            "created_at": now_utc.isoformat(),
            "ape_version": __version__,
            "research_id": f"res_{uuid.uuid4().hex[:8]}",
            "opportunity_id": f"op_{clean_topic_id}"
        }

        # Build clean ResearchReport
        report = ResearchReport(
            topic=topic,
            target_audience=combined_signals.get("target_audience", []),  # type: ignore
            competitors=combined_signals.get("competitors", []),  # type: ignore
            pain_points=pains_list,  # type: ignore
            market_signals=combined_signals.get("market_signals", []),  # type: ignore
            risks=combined_signals.get("risks", []),  # type: ignore
            confidence=conf_val,  # type: ignore
            sources=combined_signals.get("sources", ["HackerNews", "AudienceHeuristics"]),  # type: ignore
            discussions=combined_signals.get("discussions", []),  # type: ignore
            suggested_mvp=combined_signals.get("suggested_mvp", []),  # type: ignore
            timestamp=now_utc,
            next_recommended_action=action,
            metadata=metadata
        )

        self._save_artifacts(report)
        return report

    def _save_artifacts(self, report: ResearchReport) -> None:
        """Write JSON and MD files under .build/research/."""
        build_dir = self._project.root / ".build" / "research"
        build_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize name
        slug = re.sub(r'[^a-z0-9_]', '', report.topic.lower().replace(" ", "_"))
        if not slug:
            slug = "unnamed_topic"

        # 1. JSON output
        json_file = build_dir / f"{slug}.json"
        json_data = {
            "metadata": report.metadata,
            "topic": report.topic,
            "next_recommended_action": report.next_recommended_action,
            "target_audience": report.target_audience,
            "competitors": report.competitors,
            "pain_points": report.pain_points,
            "market_signals": report.market_signals,
            "risks": report.risks,
            "confidence": report.confidence,
            "sources": report.sources,
            "discussions": report.discussions,
            "suggested_mvp": report.suggested_mvp,
            "timestamp": report.timestamp.isoformat()
        }
        json_file.write_text(json.dumps(json_data, indent=2), encoding="utf-8")

        # 2. Markdown output
        md_file = build_dir / f"{slug}.md"
        
        disc_lines = []
        for d in report.discussions:
            title = d.get("title", "")
            pts = d.get("points", 0)
            url = d.get("url", "")
            disc_lines.append(f"- **{title}** (HN Points: {pts}) - {url}")

        md_content = (
            f"# Research Report: {report.topic}\n\n"
            f"**Timestamp:** {report.timestamp.isoformat()} UTC  \n"
            f"**Next Recommended Action:** {report.next_recommended_action}  \n"
            f"**Confidence Score:** {report.confidence:.0%}  \n"
            f"**Sources:** {', '.join(report.sources)}\n\n"
            "## Target Audience\n"
            + "\n".join(f"- {a}" for a in report.target_audience) + "\n\n"
            "## Competitors\n"
            + "\n".join(f"- {c}" for c in report.competitors) + "\n\n"
            "## Pain Points\n"
            + "\n".join(f"- {p}" for p in report.pain_points) + "\n\n"
            "## Market Signals\n"
            + "\n".join(f"- {s}" for s in report.market_signals) + "\n\n"
            "## Risks\n"
            + "\n".join(f"- {r}" for r in report.risks) + "\n\n"
            "## Suggested MVP\n"
            + "\n".join(f"- {m}" for m in report.suggested_mvp) + "\n\n"
            "## HackerNews Discussions\n"
            + "\n".join(disc_lines) + "\n\n"
            "## Metadata\n"
            + "\n".join(f"- **{k}:** {v}" for k, v in report.metadata.items())
        )
        md_file.write_text(md_content, encoding="utf-8")
