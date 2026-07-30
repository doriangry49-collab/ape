"""
APE Status Service — Read-only Observability & Build History Reader.
(RFC-021)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ape.project import Project
from ape.utils import slugify


@dataclass(frozen=True)
class StageStatus:
    name: str
    status: str
    details: Dict[str, Any]


@dataclass(frozen=True)
class TopicStatusReport:
    topic: str
    slug: str
    overall_status: str
    lineage_match: bool
    research: StageStatus
    decision: StageStatus
    roadmap: StageStatus
    execution: StageStatus
    release: StageStatus


@dataclass(frozen=True)
class TopicStatusSummary:
    slug: str
    topic: str
    decision: str
    execution: str
    release: str
    last_updated: str


class StatusService:
    """
    Read-only service for inspecting topic build state across .build/ artifacts
    and .governance/evidence logs.
    """

    def __init__(self, project: Project) -> None:
        self._project = project
        self._root = project.root

    def _read_json_safe(self, path: Path) -> tuple[Optional[dict], Optional[str]]:
        """Read JSON file safely without modifying anything. Returns (data, error)."""
        if not path.exists():
            return None, None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f), None
        except Exception as exc:
            return None, f"CORRUPTED ({type(exc).__name__})"

    def _get_last_release_event(self, slug: str) -> Optional[dict]:
        """Find the latest release event payload for a given topic slug in evidence logs."""
        evidence_dir = self._root / ".governance" / "evidence"
        if not evidence_dir.exists():
            return None

        # Gather all release jsonl files (including active partitioned and archive files)
        release_files = sorted(evidence_dir.rglob("*release*.jsonl"))
        matching_events = []

        for r_file in release_files:
            try:
                with open(r_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            if data.get("topic_slug") == slug:
                                matching_events.append(data)
                        except json.JSONDecodeError:
                            continue
            except Exception:
                continue

        return matching_events[-1] if matching_events else None

    def get_topic_status(self, topic_or_slug: str) -> TopicStatusReport:
        slug = slugify(topic_or_slug)
        build_dir = self._root / ".build"

        # 0. Research Stage
        res_path = build_dir / "research" / f"{slug}.json"
        res_data, res_err = self._read_json_safe(res_path)
        if res_err:
            res_stage = StageStatus("Research", "CORRUPTED", {"error": res_err})
        elif isinstance(res_data, dict):
            metadata = res_data.get("metadata") if isinstance(res_data.get("metadata"), dict) else {}
            signals = res_data.get("signals") if isinstance(res_data.get("signals"), dict) else {}
            res_stage = StageStatus("Research", "PASSED", {
                "research_id": metadata.get("research_id", "N/A") or "N/A",
                "topic": res_data.get("topic", topic_or_slug) or topic_or_slug,
                "confidence": signals.get("confidence", "N/A") if signals.get("confidence") is not None else "N/A",
                "action": res_data.get("recommended_action", "N/A") or "N/A",
            })
        else:
            res_stage = StageStatus("Research", "NOT_STARTED", {})

        # 1. Decision Stage
        dec_path = build_dir / "decisions" / f"{slug}.json"
        dec_data, dec_err = self._read_json_safe(dec_path)
        if dec_err:
            dec_stage = StageStatus("Decision", "CORRUPTED", {"error": dec_err})
        elif isinstance(dec_data, dict):
            dec_stage = StageStatus("Decision", str(dec_data.get("decision") or "UNKNOWN"), {
                "decision_id": dec_data.get("decision_id", "N/A") or "N/A",
                "policy": dec_data.get("policy", "N/A") or "N/A",
                "overall_score": dec_data.get("overall_score", 0) if dec_data.get("overall_score") is not None else 0,
                "rule_id": dec_data.get("rule_id", "N/A") or "N/A",
            })
        else:
            dec_stage = StageStatus("Decision", "NOT_STARTED", {})

        # 2. Roadmap Stage
        rm_path = build_dir / "roadmaps" / f"{slug}.json"
        rm_data, rm_err = self._read_json_safe(rm_path)
        if rm_err:
            rm_stage = StageStatus("Roadmap", "CORRUPTED", {"error": rm_err})
        elif isinstance(rm_data, dict):
            raw_milestones = rm_data.get("milestones")
            milestones = raw_milestones if isinstance(raw_milestones, list) else []
            total_tasks = 0
            for m in milestones:
                if isinstance(m, dict):
                    raw_tasks = m.get("tasks")
                    if isinstance(raw_tasks, list):
                        total_tasks += len(raw_tasks)

            rm_stage = StageStatus("Roadmap", "GENERATED", {
                "roadmap_id": rm_data.get("roadmap_id", "N/A") or "N/A",
                "decision_id": rm_data.get("decision_id", "N/A") or "N/A",
                "goal": rm_data.get("goal", "N/A") or "N/A",
                "milestone_count": len(milestones),
                "task_count": total_tasks,
            })
        else:
            rm_stage = StageStatus("Roadmap", "NOT_STARTED", {})

        # 3. Execution Stage
        exec_path = build_dir / "execution" / slug / "current.json"
        exec_data, exec_err = self._read_json_safe(exec_path)
        if exec_err:
            exec_stage = StageStatus("Execution", "CORRUPTED", {"error": exec_err})
        elif isinstance(exec_data, dict):
            raw_tasks = exec_data.get("tasks")
            tasks = raw_tasks if isinstance(raw_tasks, list) else []
            completed_count = sum(1 for t in tasks if isinstance(t, dict) and t.get("status") == "COMPLETED")
            exec_stage = StageStatus("Execution", str(exec_data.get("status") or "UNKNOWN"), {
                "execution_id": exec_data.get("execution_id", "N/A") or "N/A",
                "roadmap_id": exec_data.get("roadmap_id", "N/A") or "N/A",
                "decision_id": exec_data.get("decision_id", "N/A") or "N/A",
                "policy_decision": exec_data.get("policy_decision", "N/A") or "N/A",
                "evidence_hash": exec_data.get("evidence_hash", "N/A") or "N/A",
                "completed_tasks": completed_count,
                "total_tasks": len(tasks),
            })
        else:
            exec_stage = StageStatus("Execution", "NOT_STARTED", {})

        # 4. Release Stage (from evidence event)
        rel_event = self._get_last_release_event(slug)
        if isinstance(rel_event, dict):
            rel_stage = StageStatus("Release", str(rel_event.get("status") or "UNKNOWN"), {
                "execution_id": rel_event.get("execution_id", "N/A") or "N/A",
                "decision_id": rel_event.get("decision_id", "N/A") or "N/A",
                "evidence_hash": rel_event.get("evidence_hash", "N/A") or "N/A",
                "changed_files": rel_event.get("changed_files") if isinstance(rel_event.get("changed_files"), list) else [],
                "details": rel_event.get("details", "") or "",
            })
        else:
            rel_stage = StageStatus("Release", "NOT_STARTED", {})

        # Lineage check: Compare Decision decision_id with Execution decision_id
        lineage_match = True
        if isinstance(dec_data, dict) and isinstance(exec_data, dict):
            dec_id = dec_data.get("decision_id")
            exec_dec_id = exec_data.get("decision_id")
            if dec_id and exec_dec_id and dec_id != exec_dec_id:
                lineage_match = False

        # Display Topic Name
        topic_name = topic_or_slug
        if isinstance(res_data, dict) and res_data.get("topic"):
            topic_name = res_data["topic"]
        elif isinstance(exec_data, dict) and exec_data.get("topic"):
            topic_name = exec_data["topic"]

        # Calculate Overall Status
        has_any_artifact = bool(res_data or dec_data or rm_data or exec_data or rel_event or res_err or dec_err or rm_err or exec_err)
        if not has_any_artifact:
            overall = "NOT_FOUND"
        elif rel_stage.status == "COMMITTED":
            overall = "COMMITTED"
        elif exec_stage.status == "COMPLETED":
            overall = "EXECUTED"
        elif exec_stage.status == "IN_PROGRESS":
            overall = "EXECUTING"
        elif exec_stage.status == "FAILED" or rel_stage.status == "FAILED":
            overall = "FAILED"
        elif exec_stage.status == "BLOCKED" or dec_stage.status in ("WATCH", "IGNORE"):
            overall = "BLOCKED"
        elif rm_stage.status == "GENERATED":
            overall = "PLANNED"
        elif dec_stage.status in ("BUILD", "VALIDATE"):
            overall = "DECIDED"
        elif res_stage.status == "PASSED":
            overall = "RESEARCHED"
        else:
            overall = "UNKNOWN"

        return TopicStatusReport(
            topic=topic_name,
            slug=slug,
            overall_status=overall,
            lineage_match=lineage_match,
            research=res_stage,
            decision=dec_stage,
            roadmap=rm_stage,
            execution=exec_stage,
            release=rel_stage,
        )

    def list_all_topics(self) -> List[TopicStatusSummary]:
        build_dir = self._root / ".build"
        slugs = set()

        if build_dir.exists():
            # Scan decisions
            dec_dir = build_dir / "decisions"
            if dec_dir.exists():
                for p in dec_dir.glob("*.json"):
                    slugs.add(p.stem)

            # Scan roadmaps
            rm_dir = build_dir / "roadmaps"
            if rm_dir.exists():
                for p in rm_dir.glob("*.json"):
                    slugs.add(p.stem)

            # Scan execution
            exec_dir = build_dir / "execution"
            if exec_dir.exists():
                for p in exec_dir.iterdir():
                    if p.is_dir() and (p / "current.json").exists():
                        slugs.add(p.name)

            # Scan research
            res_dir = build_dir / "research"
            if res_dir.exists():
                for p in res_dir.glob("*.json"):
                    slugs.add(p.stem)

        summaries = []
        for slug in sorted(slugs):
            report = self.get_topic_status(slug)
            last_updated = "N/A"
            # Get timestamp if available
            exec_path = build_dir / "execution" / slug / "current.json"
            if exec_path.exists():
                try:
                    last_updated = exec_path.stat().st_mtime
                    from datetime import datetime, timezone
                    last_updated = datetime.fromtimestamp(last_updated, timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
                except Exception:
                    pass

            summaries.append(TopicStatusSummary(
                slug=report.slug,
                topic=report.topic,
                decision=report.decision.status,
                execution=report.execution.status,
                release=report.release.status,
                last_updated=str(last_updated),
            ))

        return summaries
