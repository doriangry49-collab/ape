from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, List, Optional

from ape.intelligence.models import Opportunity
from ape.utils import slugify


class ScanPersistenceService:
    """
    Persists scanned market and tech opportunities into structured .build/scans/ artifacts,
    establishing an immutable audit trail and discovery lineage.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.scans_dir = self.project_root / ".build" / "scans"

    def _ensure_directory(self) -> Path:
        self.scans_dir.mkdir(parents=True, exist_ok=True)
        return self.scans_dir

    def serialize_opportunity(self, opp: Opportunity) -> dict[str, Any]:
        """Convert frozen dataclass Opportunity into JSON-serializable dictionary."""
        pain_dict: Optional[dict[str, Any]] = None
        if opp.pain_point:
            pain_dict = {
                "domain": opp.pain_point.domain,
                "description": opp.pain_point.description,
                "frequency_signal": str(opp.pain_point.frequency_signal),
                "payment_signal": str(opp.pain_point.payment_signal),
                "ai_solvable": str(opp.pain_point.ai_solvable),
            }

        return {
            "title": opp.title,
            "slug": slugify(opp.title),
            "description": opp.description,
            "url": opp.url,
            "source": opp.source,
            "score": opp.score,
            "confidence": opp.confidence,
            "published_at": opp.published_at.isoformat() if isinstance(opp.published_at, datetime) else str(opp.published_at),
            "tags": opp.tags,
            "is_hypothesis": opp.is_hypothesis,
            "pain_point": pain_dict,
            "business_evidence_count": len(opp.business_evidence) if opp.business_evidence else 0,
        }

    def save_scan(self, opportunities: List[Opportunity], mode: str = "tech", timestamp: Optional[datetime] = None) -> tuple[Path, Path]:
        """
        Saves opportunities to .build/scans/YYYY-MM-DD-<mode>-scan.json and .md.
        Returns tuple of (json_path, md_path).
        """
        self._ensure_directory()
        now = timestamp or datetime.now(UTC)
        date_str = now.strftime("%Y-%m-%d")
        base_name = f"{date_str}-{mode}-scan"

        json_path = self.scans_dir / f"{base_name}.json"
        md_path = self.scans_dir / f"{base_name}.md"

        serialized_ops = [self.serialize_opportunity(op) for op in opportunities]

        scan_payload: dict[str, Any] = {
            "metadata": {
                "schema_version": "1.0",
                "mode": mode,
                "scanned_at": now.isoformat(),
                "total_opportunities": len(serialized_ops),
            },
            "opportunities": serialized_ops,
        }

        # 1. Write canonical JSON artifact
        json_path.write_text(json.dumps(scan_payload, indent=2), encoding="utf-8")

        # 2. Write companion Markdown artifact
        md_lines = [
            f"# APE Discovery Scan Report: {mode.upper()}",
            f"",
            f"**Scanned At:** `{now.strftime('%Y-%m-%d %H:%M:%S')} UTC`  ",
            f"**Mode:** `{mode}`  ",
            f"**Total Opportunities Discovered:** `{len(serialized_ops)}`  ",
            f"",
            "---",
            "",
            "| # | Title | Source | Score | Confidence | URL |",
            "| :-: | :--- | :--- | :-: | :-: | :--- |",
        ]

        for idx, op in enumerate(serialized_ops, start=1):
            title = op["title"].replace("|", "-")
            source = op["source"]
            score = op["score"]
            conf = f"{op['confidence'] * 100:.0f}%" if isinstance(op['confidence'], (float, int)) else str(op['confidence'])
            url = op["url"]
            md_lines.append(f"| {idx} | {title} | `{source}` | **{score}** | {conf} | [{url}]({url}) |")

        md_lines.append("")
        md_path.write_text("\n".join(md_lines), encoding="utf-8")

        return json_path, md_path

    def list_scans(self) -> List[Path]:
        """List all scan JSON artifact paths sorted newest first."""
        if not self.scans_dir.exists():
            return []
        return sorted(self.scans_dir.glob("*-scan.json"), reverse=True)
