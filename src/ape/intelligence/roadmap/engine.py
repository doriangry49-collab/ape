import json
import uuid
from pathlib import Path

from ape.intelligence.execution.policy import CANONICAL_ACTIONS
from ape.intelligence.roadmap.llm import OpenAICompatibleProvider
from ape.intelligence.roadmap.models import Milestone, Roadmap, Task
from ape.intelligence.roadmap.planner import IntelligentPlanner
from ape.project import Project
from ape.services.config_service import ConfigService
from ape.utils import append_to_evidence, get_current_artifact


class RoadmapGenerator:
    """
    Reads the current-state decision artifact (O(1) canonical pointer) and
    generates an execution roadmap.

    Artifact model:
      Current state  -> .build/roadmaps/<slug>.json   (mutable)
      Immutable log  -> .governance/evidence/roadmaps-YYYY-MM.jsonl  (append-only)
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_service = ConfigService(Project.load(project_root))

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

        # Attempt to use IntelligentPlanner if configured
        api_key = self.config_service.planner_api_key
        if api_key:
            provider = OpenAICompatibleProvider(
                api_key=api_key,
                model=self.config_service.planner_model,
                base_url=self.config_service.planner_base_url or "https://api.openai.com/v1"
            )
            planner = IntelligentPlanner(provider)
            try:
                proposal = planner.generate_proposal(
                    topic=topic,
                    decision_id=decision_id,
                    policy_decision=decision_val,
                    evidence_context=json.dumps(decision_data.get("evidence", {}))
                )
                
                # Lineage & Policy Check
                if proposal.decision_id != decision_id:
                    raise ValueError(f"Lineage mismatch: Planner changed decision_id to {proposal.decision_id}")
                if proposal.policy_decision != decision_val:
                    raise ValueError(f"Policy mutation: Planner changed policy_decision to {proposal.policy_decision}")
                
                # Action whitelist validation against Canonical Action Vocabulary
                # Prevent prompt injection from crafting arbitrary execution steps.
                for ms in proposal.milestones:
                    for tsk in ms.tasks:
                        if tsk.action not in CANONICAL_ACTIONS:
                            raise ValueError(f"Unauthorized action proposed: {tsk.action}. Must be one of {CANONICAL_ACTIONS}")

                milestones = []
                for p_ms in proposal.milestones:
                    tasks = []
                    for p_tsk in p_ms.tasks:
                        tasks.append(
                            Task(
                                task_id=p_tsk.task_id,
                                description=p_tsk.description,
                                deliverables=p_tsk.deliverables,
                                estimated_effort=p_tsk.estimated_effort,
                                action=p_tsk.action
                            )
                        )
                    milestones.append(
                        Milestone(
                            milestone_id=p_ms.milestone_id,
                            title=p_ms.title,
                            tasks=tasks,
                            dependencies=p_ms.dependencies
                        )
                    )
                
                estimated_time = "Dynamic Plan (LLM Estimated)"
                risks = ["LLM proposed plan - monitor execution"]
                generator_meta = "intelligent-planner"
                
                return self._finalize_roadmap(
                    roadmap_id, decision_id, decision_val, policy, topic, topic_slug,
                    milestones, estimated_time, risks, generator_meta
                )

            except Exception as e:
                print(f"Intelligent planning failed ({e}). Falling back to deterministic templates.")
                # Fallthrough to deterministic generator

        # Deterministic Fallback
        return self._generate_deterministic_fallback(
            roadmap_id, decision_id, decision_val, policy, topic, topic_slug
        )

    def _generate_deterministic_fallback(
        self, roadmap_id: str, decision_id: str, decision_val: str, policy: str, topic: str, topic_slug: str
    ) -> Roadmap:
        # RFC-014: Generate policy-appropriate milestones.
        # BUILD → MVP development track. VALIDATE → Market validation track.
        if decision_val == "VALIDATE":
            milestones = [
                Milestone(
                    milestone_id="ms_1",
                    title="Problem Validation",
                    tasks=[
                        Task(
                            task_id="tsk_1_1",
                            description="Conduct user interviews to validate pain points",
                            deliverables=["Interview Notes", "Pain Point Summary"],
                            estimated_effort="3 days"
                        ),
                        Task(
                            task_id="tsk_1_2",
                            description="Map identified pain points to potential solution areas",
                            deliverables=["Pain Point Map"],
                            estimated_effort="1 day"
                        ),
                    ],
                    dependencies=[]
                ),
                Milestone(
                    milestone_id="ms_2",
                    title="Signal Testing",
                    tasks=[
                        Task(
                            task_id="tsk_2_1",
                            description="Build and deploy a landing page with waitlist sign-up",
                            deliverables=["Landing Page URL", "Waitlist Form"],
                            estimated_effort="2 days"
                        ),
                        Task(
                            task_id="tsk_2_2",
                            description="Deploy targeted survey to potential customer segment",
                            deliverables=["Survey Results Report"],
                            estimated_effort="3 days"
                        ),
                    ],
                    dependencies=["ms_1"]
                ),
                Milestone(
                    milestone_id="ms_3",
                    title="Evidence Review",
                    tasks=[
                        Task(
                            task_id="tsk_3_1",
                            description="Analyze collected signals against success criteria",
                            deliverables=["Validation Decision Document"],
                            estimated_effort="1 day"
                        ),
                    ],
                    dependencies=["ms_2"]
                ),
            ]
            estimated_time = "1 week"
            risks = ["Low engagement on landing page", "Survey bias"]

        else:
            # BUILD
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
                        ),
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
                        ),
                    ],
                    dependencies=["ms_1"]
                ),
                Milestone(
                    milestone_id="ms_3",
                    title="Launch & Validation",
                    tasks=[
                        Task(
                            task_id="tsk_3_1",
                            description="Verify build artifacts and run test suite",
                            deliverables=["Test Verification Log"],
                            estimated_effort="1 day",
                            action="run_tests"
                        ),
                        Task(
                            task_id="tsk_3_2",
                            description="Monitor analytics and gather feedback",
                            deliverables=["Analytics Dashboard", "User Feedback Report"],
                            estimated_effort="Ongoing",
                            action="read_file"
                        ),
                    ],
                    dependencies=["ms_2"]
                ),
            ]
            estimated_time = "1-2 weeks"
            risks = ["Scope creep during MVP", "Technical debt accumulation"]

        return self._finalize_roadmap(
            roadmap_id, decision_id, decision_val, policy, topic, topic_slug,
            milestones, estimated_time, risks, "heuristic-template"
        )

    def _finalize_roadmap(
        self, roadmap_id: str, decision_id: str, decision_val: str, policy: str,
        topic: str, topic_slug: str, milestones: list, estimated_time: str,
        risks: list, generator_meta: str
    ) -> Roadmap:
        roadmap = Roadmap(
            roadmap_id=roadmap_id,
            decision_id=decision_id,
            policy_decision=decision_val,
            goal=f"Execute {policy} for {topic}",
            milestones=milestones,
            estimated_time=estimated_time,
            risks=risks,
            metadata={"generator": generator_meta, "version": "1.2"}
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
