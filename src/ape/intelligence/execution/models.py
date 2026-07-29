"""Execution Engine — Data Models."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    PAUSED = "PAUSED"
    BLOCKED = "BLOCKED"


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"


@dataclass
class ExecutionTask:
    task_id: str
    description: str
    deliverables: List[str]
    action: str = "create_file"
    status: TaskStatus = field(default=TaskStatus.PENDING)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "action": self.action,
            "deliverables": self.deliverables,
            "status": self.status.value,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ExecutionTask":
        return cls(
            task_id=d["task_id"],
            description=d["description"],
            deliverables=d.get("deliverables", []),
            action=d.get("action", "create_file"),
            status=TaskStatus(d.get("status", "PENDING")),
            error=d.get("error"),
        )


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ExecutionState:
    execution_id: str
    roadmap_id: str
    topic: str
    tasks: List[ExecutionTask]
    # RFC-014: Decision audit lineage — carried from DecisionReport via Roadmap.
    # Defaults to "UNKNOWN" for backward compatibility with existing state files.
    decision_id: str = "UNKNOWN"
    policy_decision: str = "UNKNOWN"  # "BUILD" | "VALIDATE" | "UNKNOWN"
    evidence_hash: str = ""
    status: ExecutionStatus = ExecutionStatus.IN_PROGRESS
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "roadmap_id": self.roadmap_id,
            "decision_id": self.decision_id,
            "policy_decision": self.policy_decision,
            "evidence_hash": self.evidence_hash,
            "topic": self.topic,
            "status": self.status.value,
            "tasks": [t.to_dict() for t in self.tasks],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ExecutionState":
        return cls(
            execution_id=d["execution_id"],
            roadmap_id=d["roadmap_id"],
            topic=d["topic"],
            tasks=[ExecutionTask.from_dict(t) for t in d.get("tasks", [])],
            decision_id=d.get("decision_id", "UNKNOWN"),
            policy_decision=d.get("policy_decision", "UNKNOWN"),
            evidence_hash=d.get("evidence_hash", ""),
            status=ExecutionStatus(d.get("status", "IN_PROGRESS")),
            created_at=d.get("created_at", _utcnow()),
            updated_at=d.get("updated_at", _utcnow()),
        )
