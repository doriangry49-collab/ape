from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, List, Optional, Tuple

from ape import __version__
from ape.intelligence.models import Opportunity
from ape.utils import append_to_evidence, slugify


class ScanPersistence:
    """Lightweight persistence manager for scan artifacts under .build/scans/."""

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._scans_dir = project_root / ".build" / "scans"
        self._evidence_dir = project_root / ".governance" / "evidence"

    @property
    def scans_dir(self) -> Path:
        return self._scans_dir

    def save_scan(
        self,
        opportunities: List[Opportunity],
        mode: str = "tech",
        timestamp: Optional[datetime] = None,
    ) -> Tuple[Path, Path]:
        """Save list of Opportunity objects to JSON & MD artifacts under .build/scans/.

        Returns (json_path, md_path).
        """
        self._scans_dir.mkdir(parents=True, exist_ok=True)
        now = timestamp or datetime.now(UTC)
        date_str = now.strftime("%Y-%m-%d")

        json_file = self._scans_dir / f"{date_str}-{mode}-scan.json"
        md_file = self._scans_dir / f"{date_str}-{mode}-scan.md"

        opps_payload = []
        for op in opportunities:
            opp_dict: dict[str, Any] = {
                "title": op.title,
                "slug": slugify(op.title),
                "description": op.description,
                "url": op.url,
                "source": op.source,
                "score": op.score,
                "confidence": op.confidence,
                "published_at": op.published_at.isoformat() if isinstance(op.published_at, datetime) else str(op.published_at),
                "tags": op.tags,
                "is_hypothesis": op.is_hypothesis,
            }
            if op.pain_point:
                opp_dict["pain_point"] = {
                    "domain": str(op.pain_point.domain),
                    "description": str(op.pain_point.description),
                    "frequency_signal": str(op.pain_point.frequency_signal),
                    "payment_signal": str(op.pain_point.payment_signal),
                    "ai_solvable": str(op.pain_point.ai_solvable),
                }
            if op.business_evidence:
                opp_dict["business_evidence_count"] = len(op.business_evidence)

            opps_payload.append(opp_dict)

        payload = {
            "metadata": {
                "schema_version": "1.0",
                "mode": mode,
                "scanned_at": now.isoformat(),
                "ape_version": __version__,
                "total_opportunities": len(opportunities),
            },
            "opportunities": opps_payload,
        }

        # 1. Canonical mutable JSON artifact
        json_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        # 2. Append-only governance audit log
        append_to_evidence(self._evidence_dir, "scans", payload)

        # 3. Human-readable Markdown summary
        md_lines = [
            f"# APE Market Scan Briefing ({mode.upper()} mode)",
            "",
            f"**Scanned At:** `{now.isoformat()}`  ",
            f"**Total Discovered:** `{len(opportunities)}`  ",
            "",
            "## Opportunities Overview",
            "",
        ]

        if not opportunities:
            md_lines.append("*No opportunities found during this scan cycle.*")
        else:
            for i, op in enumerate(opportunities, start=1):
                md_lines.append(f"### {i}. {op.title}")
                md_lines.append(f"- **Source:** {op.source}")
                md_lines.append(f"- **Score:** {op.score}/100")
                md_lines.append(f"- **URL:** {op.url}")
                if op.pain_point:
                    md_lines.append(f"- **Pain Domain:** {op.pain_point.domain}")
                    md_lines.append(f"- **Pain Detail:** {op.pain_point.description}")
                md_lines.append("")

        md_file.write_text("\n".join(md_lines), encoding="utf-8")

        return json_file, md_file

    def load_latest_scan(self, mode: Optional[str] = None) -> Optional[dict[str, Any]]:
        """Find and return the latest JSON scan data, optionally filtered by mode."""
        if not self._scans_dir.exists():
            return None

        pattern = f"*-{mode}-scan.json" if mode else "*-scan.json"
        json_files = sorted(self._scans_dir.glob(pattern), reverse=True)

        if not json_files:
            return None

        try:
            return json.loads(json_files[0].read_text(encoding="utf-8"))
        except Exception:
            return None

    def find_matching_opportunity(
        self, topic: str
    ) -> Tuple[Optional[dict[str, Any]], Optional[dict[str, Any]], Optional[Path]]:
        """Search .build/scans/*.json sorted by date descending for an opportunity matching topic.

        Returns (matched_opportunity_dict, scan_metadata_dict, json_file_path).
        Safely handles malformed/corrupt JSON files without crashing.
        """
        if not self._scans_dir.exists():
            return None, None, None

        topic_clean = topic.strip().lower()
        topic_slug = slugify(topic_clean)

        # Deterministic sorting: newest scan files first (by path reverse)
        json_files = sorted(self._scans_dir.glob("*-scan.json"), reverse=True)

        for json_path in json_files:
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
            except Exception:
                # Malformed JSON artifact: skip safely
                continue

            if not isinstance(data, dict):
                continue

            metadata = data.get("metadata", {})
            opportunities = data.get("opportunities", [])
            if not isinstance(opportunities, list):
                continue

            for opp in opportunities:
                if not isinstance(opp, dict):
                    continue

                opp_slug = str(opp.get("slug", "")).lower()
                opp_title = str(opp.get("title", "")).lower()
                opp_tags = [str(t).lower() for t in opp.get("tags", []) if isinstance(t, str)]

                # Deterministic matching rules:
                # 1. Exact match on slug
                # 2. Exact match on tag
                # 3. Substring match on title/topic
                if (
                    (topic_slug and opp_slug == topic_slug)
                    or (topic_clean in opp_tags)
                    or (topic_clean and topic_clean in opp_title)
                    or (opp_title and opp_title in topic_clean)
                ):
                    return opp, metadata, json_path

        return None, None, None
