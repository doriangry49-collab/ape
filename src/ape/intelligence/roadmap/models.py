from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List


def _now_utc():
    return datetime.now(timezone.utc)

@dataclass(frozen=True)
class Task:
    task_id: str
    description: str
    deliverables: List[str]
    estimated_effort: str
    action: str = ""

    def to_dict(self) -> dict:
        d = {
            "task_id": self.task_id,
            "description": self.description,
            "deliverables": self.deliverables,
            "estimated_effort": self.estimated_effort
        }
        if self.action:
            d["action"] = self.action
        return d

@dataclass(frozen=True)
class Milestone:
    milestone_id: str
    title: str
    tasks: List[Task]
    dependencies: List[str]

    def to_dict(self) -> dict:
        return {
            "milestone_id": self.milestone_id,
            "title": self.title,
            "tasks": [t.to_dict() for t in self.tasks],
            "dependencies": self.dependencies
        }

@dataclass(frozen=True)
class Roadmap:
    roadmap_id: str
    decision_id: str
    goal: str
    milestones: List[Milestone]
    estimated_time: str
    risks: List[str]
    # RFC-014: Carries the originating PolicyDecision ("BUILD" | "VALIDATE") so
    # ExecutionEngine can read policy semantics without re-opening the decision artifact.
    policy_decision: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=_now_utc)

    def to_dict(self) -> dict:
        return {
            "roadmap_id": self.roadmap_id,
            "decision_id": self.decision_id,
            "policy_decision": self.policy_decision,
            "goal": self.goal,
            "milestones": [m.to_dict() for m in self.milestones],
            "estimated_time": self.estimated_time,
            "risks": self.risks,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() + "Z"
        }

