import json
import uuid
from pathlib import Path

from ape.intelligence.roadmap.models import Milestone, Roadmap, Task
from ape.utils import append_to_evidence, get_current_artifact


class RoadmapGenerator:
    """
    Reads the current-state decision artifact (O(1) canonical pointer) and
    generates an execution roadmap.

    Artifact model:
      Current state  -> .build/roadmaps/<slug>.json   (mutable)
      Immutable log  -> .governance/evidence/roadmaps.jsonl  (append-only)
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def generate_roadmap(self, topic: str, topic_slug: str) -> Roadmap:
        decisions_dir = self.project_root / ".build" / "decisions"
        decision_file = get_current_artifact(decisions_dir, topic_slug)

        if not decision_file:
            raise FileNotFoundError(
                f"Decision report not found for topic: {topic_slug}. "
                "Run `ape decide` first."
            )

        with open(decision_file, "r", encoding="utf-8") as f:
            decision_data = json.loads(f.read())

        decision_id = decision_data.get("decision_id", "UNKNOWN")
        decision_val = str(decision_data.get("decision", "")).upper()
        policy = decision_data.get("policy", "")

        if decision_val in ("WATCH", "IGNORE", "BLOCKED"):
            msg = (
                f"Cannot generate roadmap for policy decision: {decision_val}. "
                "Must be BUILD or VALIDATE related."
            )
            raise ValueError(msg)

        if "BUILD" not in policy and "VALIDATE" not in policy and decision_val not in ("BUILD", "VALIDATE"):
            msg = (
                f"Cannot generate roadmap for policy: {policy} (decision: {decision_val}). "
                "Must be BUILD or VALIDATE related."
            )
            raise ValueError(msg)

        roadmap_id = f"rm_{uuid.uuid4().hex[:8]}"

        milestones = [
            Milestone(
                milestone_id="ms_1",
                title="Design & Architecture",
                tasks=[
                    Task(
                        task_id="tsk_1_1",
                        description="Define core data models and architecture",
                        deliverables=["Architecture Document", "Data Models"],
                        estimated_effort="1 day"
                    ),
                    Task(
                        task_id="tsk_1_2",
                        description="Setup project repository and CI/CD",
                        deliverables=["Git Repo", "Github Actions"],
                        estimated_effort="4 hours"
                    )
                ],
                dependencies=[]
            ),
            Milestone(
                milestone_id="ms_2",
                title="MVP Development",
                tasks=[
                    Task(
                        task_id="tsk_2_1",
                        description="Implement core backend logic",
                        deliverables=["API Endpoints", "Core Engine"],
                        estimated_effort="3 days"
                    ),
                    Task(
                        task_id="tsk_2_2",
                        description="Implement basic CLI or Web UI",
                        deliverables=["User Interface"],
                        estimated_effort="2 days"
                    )
                ],
                dependencies=["ms_1"]
            ),
            Milestone(
                milestone_id="ms_3",
                title="Launch & Validation",
                tasks=[
                    Task(
                        task_id="tsk_3_1",
                        description="Deploy to production environment",
                        deliverables=["Live URL", "Deployment scripts"],
                        estimated_effort="1 day"
                    ),
                    Task(
                        task_id="tsk_3_2",
                        description="Monitor analytics and gather feedback",
                        deliverables=["Analytics Dashboard", "User Feedback Report"],
                        estimated_effort="Ongoing"
                    )
                ],
                dependencies=["ms_2"]
            )
        ]

        roadmap = Roadmap(
            roadmap_id=roadmap_id,
            decision_id=decision_id,
            goal=f"Execute {policy} for {topic}",
            milestones=milestones,
            estimated_time="1-2 weeks",
            risks=["Scope creep during MVP", "Technical debt accumulation"],
            metadata={"generator": "heuristic-template", "version": "1.0"}
        )

        self._save_artifacts(topic_slug, roadmap)
        return roadmap

    def _save_artifacts(self, topic_slug: str, roadmap: Roadmap) -> None:
        roadmaps_dir = self.project_root / ".build" / "roadmaps"
        roadmaps_dir.mkdir(parents=True, exist_ok=True)

        report_dict = roadmap.to_dict()

        # 1. Current state (canonical pointer - mutable)
        json_path = roadmaps_dir / f"{topic_slug}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)

        # 2. Evidence history (append-only)
        evidence_dir = self.project_root / ".governance" / "evidence"
        append_to_evidence(evidence_dir, "roadmaps", report_dict)

        # 3. Markdown (current state - mutable)
        md_path = roadmaps_dir / f"{topic_slug}.md"
        md_content = [
            f"# Execution Roadmap: {roadmap.goal}",
            f"**Roadmap ID:** `{roadmap.roadmap_id}`",
            f"**Decision ID:** `{roadmap.decision_id}`",
            f"**Estimated Time:** {roadmap.estimated_time}",
            "",
            "## Milestones"
        ]

        for ms in roadmap.milestones:
            md_content.append(f"### Milestone: {ms.title} (`{ms.milestone_id}`)")
            if ms.dependencies:
                md_content.append(f"*(Depends on: {', '.join(ms.dependencies)})*")
            for tsk in ms.tasks:
                md_content.append(
                    f"- **Task:** {tsk.description} (Effort: {tsk.estimated_effort})"
                )
                md_content.append(f"  - Deliverables: {', '.join(tsk.deliverables)}")
            md_content.append("")

        md_content.append("## Risks")
        for risk in roadmap.risks:
            md_content.append(f"- {risk}")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))
