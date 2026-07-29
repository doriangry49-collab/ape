"""
Contracts for Intelligent Planning Boundary.
(RFC-015)
"""
from dataclasses import dataclass
from typing import List


@dataclass
class PlannerTask:
    task_id: str
    description: str
    action: str  # e.g., create_file, modify_file, etc. (must be whitelisted)
    deliverables: List[str]
    estimated_effort: str

@dataclass
class PlannerMilestone:
    milestone_id: str
    title: str
    tasks: List[PlannerTask]
    dependencies: List[str]

@dataclass
class PlannerProposal:
    decision_id: str
    policy_decision: str
    reasoning: str
    milestones: List[PlannerMilestone]

    @classmethod
    def from_dict(cls, data: dict) -> "PlannerProposal":
        milestones = []
        for m in data.get("milestones", []):
            tasks = []
            for t in m.get("tasks", []):
                tasks.append(
                    PlannerTask(
                        task_id=t.get("task_id", ""),
                        description=t.get("description", ""),
                        action=t.get("action", ""),
                        deliverables=t.get("deliverables", []),
                        estimated_effort=t.get("estimated_effort", "")
                    )
                )
            milestones.append(
                PlannerMilestone(
                    milestone_id=m.get("milestone_id", ""),
                    title=m.get("title", ""),
                    tasks=tasks,
                    dependencies=m.get("dependencies", [])
                )
            )
            
        return cls(
            decision_id=data.get("decision_id", ""),
            policy_decision=data.get("policy_decision", ""),
            reasoning=data.get("reasoning", ""),
            milestones=milestones
        )

# Strict JSON Schema to inject into the LLM context
PLANNER_PROPOSAL_SCHEMA = {
    "type": "object",
    "properties": {
        "decision_id": {
            "type": "string",
            "description": "Must exactly match the provided decision_id."
        },
        "policy_decision": {
            "type": "string",
            "description": "Must exactly match the provided policy_decision (e.g. BUILD or VALIDATE)."
        },
        "reasoning": {
            "type": "string",
            "description": "A brief explanation of why this roadmap was proposed based on evidence."
        },
        "milestones": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "milestone_id": {"type": "string"},
                    "title": {"type": "string"},
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "tasks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "string"},
                                "description": {"type": "string"},
                                "action": {
                                    "type": "string",
                                    "description": "Action type (e.g. create_file, modify_file, read_file). Do NOT use shell_command."
                                },
                                "deliverables": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "estimated_effort": {"type": "string"}
                            },
                            "required": ["task_id", "description", "action", "deliverables", "estimated_effort"]
                        }
                    }
                },
                "required": ["milestone_id", "title", "dependencies", "tasks"]
            }
        }
    },
    "required": ["decision_id", "policy_decision", "reasoning", "milestones"]
}
