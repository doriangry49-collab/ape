"""
Agent Lifecycle & State Machine — RFC-022 / PR-A2 Specification.
Defines AgentStatus Enum and AgentLifecycle state machine for Fabric Agents.
"""

from enum import Enum
from typing import Dict, Optional


class AgentStatus(str, Enum):
    """Lifecycle status enum for Fabric Agents."""
    IDLE = "IDLE"
    ASSIGNED = "ASSIGNED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"


class InvalidAgentTransitionError(Exception):
    """Raised when an illegal lifecycle state transition is attempted."""
    pass


class AgentLifecycle:
    """Manages lifecycle transitions and invariants for a Fabric Agent."""

    VALID_TRANSITIONS: Dict[AgentStatus, set[AgentStatus]] = {
        AgentStatus.IDLE: {AgentStatus.ASSIGNED, AgentStatus.EXECUTING},
        AgentStatus.ASSIGNED: {AgentStatus.EXECUTING, AgentStatus.PAUSED, AgentStatus.FAILED},
        AgentStatus.EXECUTING: {AgentStatus.COMPLETED, AgentStatus.FAILED, AgentStatus.PAUSED},
        AgentStatus.PAUSED: {AgentStatus.EXECUTING, AgentStatus.FAILED},
        AgentStatus.COMPLETED: set(),  # Terminal state
        AgentStatus.FAILED: set(),     # Terminal state
    }

    def __init__(self, agent_name: str, role: str) -> None:
        self.agent_name = agent_name
        self.role = role
        self.status = AgentStatus.IDLE
        self.failure_reason: Optional[str] = None

    def transition_to(self, new_status: AgentStatus, reason: Optional[str] = None) -> None:
        """Transition agent lifecycle state with invariant checks."""
        allowed = self.VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidAgentTransitionError(
                f"Agent '{self.agent_name}' ({self.role}) cannot transition from {self.status.value} to {new_status.value}"
            )
        self.status = new_status
        if reason:
            self.failure_reason = reason
