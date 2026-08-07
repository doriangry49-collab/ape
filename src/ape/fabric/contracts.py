"""
Agent Fabric SDK Constitutional Contracts — RFC-022 / PR-A1 Specification.
Defines ApeAgent Protocol interface for specialized Fabric Agents.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol, runtime_checkable


@dataclass
class AgentReport:
    """Standardized report returned by an ApeAgent execution."""
    agent_name: str
    role: str
    status: str  # COMPLETED, FAILED, PAUSED
    outputs: Dict[str, Any] = field(default_factory=dict)
    findings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    evidence_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "role": self.role,
            "status": self.status,
            "outputs": self.outputs,
            "findings": self.findings,
            "errors": self.errors,
            "evidence_hash": self.evidence_hash,
        }


@runtime_checkable
class ApeAgent(Protocol):
    """Constitutional Protocol contract that all APE Fabric Agents must implement."""

    role: str
    capabilities: List[str]

    @property
    def name(self) -> str:
        """Unique instance or class name of the agent."""
        ...

    def execute(self, workspace_context: Any) -> AgentReport:
        """Execute agent's primary task within shared workspace memory."""
        ...

    def explain(self) -> str:
        """Return human-readable explanation of agent role and decision logic."""
        ...

    def observe(self, event: Any) -> None:
        """Receive and process real-time events from ObservationBus."""
        ...

    def report(self) -> AgentReport:
        """Return latest AgentReport."""
        ...
