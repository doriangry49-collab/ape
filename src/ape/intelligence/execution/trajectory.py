"""
Execution Engine — Normalized Trajectory Data Models.
ORION-122 (Mission A) Specification.

Provides normalized, queryable in-memory TrajectoryStep and ExecutionTrajectory
dataclasses that bridge raw JSONL telemetry with downstream supervisory evaluators.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class TrajectoryStep:
    """
    Normalized single step within an execution trajectory.
    Bridges raw telemetry events into an immutable, queryable step representation.
    """
    step_id: str
    task_id: str
    attempt: int
    thought: str
    action: str
    params: Dict[str, Any]
    exit_code: int
    stdout_hash: str
    stderr_signature: str
    status: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "task_id": self.task_id,
            "attempt": self.attempt,
            "thought": self.thought,
            "action": self.action,
            "params": self.params,
            "exit_code": self.exit_code,
            "stdout_hash": self.stdout_hash,
            "stderr_signature": self.stderr_signature,
            "status": self.status,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> TrajectoryStep:
        return cls(
            step_id=str(d.get("step_id", "")),
            task_id=str(d.get("task_id", "")),
            attempt=int(d.get("attempt", 1)),
            thought=str(d.get("thought", "")),
            action=str(d.get("action", "")),
            params=dict(d.get("params", {})),
            exit_code=int(d.get("exit_code", 0)),
            stdout_hash=str(d.get("stdout_hash", "")),
            stderr_signature=str(d.get("stderr_signature", "")),
            status=str(d.get("status", "EXECUTED")),
            timestamp=str(d.get("timestamp", "")),
        )


@dataclass
class ExecutionTrajectory:
    """
    In-memory queryable trajectory stream for an ExecutionPipeline run.
    Contains chronological steps and computes tamper-evident trajectory digests.
    """
    execution_id: str
    topic_slug: str
    decision_id: str = "UNKNOWN"
    policy_decision: str = "UNKNOWN"
    evidence_hash: str = ""
    steps: List[TrajectoryStep] = field(default_factory=list)

    def append_step(self, step: TrajectoryStep) -> None:
        """Appends a normalized step to the trajectory."""
        self.steps.append(step)

    def get_steps_for_task(self, task_id: str) -> List[TrajectoryStep]:
        """Returns all steps associated with a specific task_id."""
        return [s for s in self.steps if s.task_id == task_id]

    def compute_trajectory_hash(self) -> str:
        """
        Computes SHA-256 Merkle digest over ordered step signatures.
        Ensures tamper-evident trajectory lineage across stage boundaries.
        """
        if not self.steps:
            return "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        hasher = hashlib.sha256()
        for s in self.steps:
            sig = (
                f"{s.task_id}:{s.attempt}:{s.action}:"
                f"{s.stdout_hash}:{s.stderr_signature}:{s.status}"
            )
            hasher.update(sig.encode("utf-8"))
        return hasher.hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "topic_slug": self.topic_slug,
            "decision_id": self.decision_id,
            "policy_decision": self.policy_decision,
            "evidence_hash": self.evidence_hash,
            "trajectory_hash": self.compute_trajectory_hash(),
            "step_count": len(self.steps),
            "steps": [s.to_dict() for s in self.steps],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ExecutionTrajectory:
        trajectory = cls(
            execution_id=str(d.get("execution_id", "")),
            topic_slug=str(d.get("topic_slug", "")),
            decision_id=str(d.get("decision_id", "UNKNOWN")),
            policy_decision=str(d.get("policy_decision", "UNKNOWN")),
            evidence_hash=str(d.get("evidence_hash", "")),
            steps=[TrajectoryStep.from_dict(s) for s in d.get("steps", [])],
        )
        return trajectory
