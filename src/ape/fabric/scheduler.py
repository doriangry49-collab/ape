"""
Agent Scheduler & Handoff Engine — RFC-022 / PR-A3 Specification.
Orchestrates multi-agent execution sequences and handoffs across Fabric Agents.
"""

from __future__ import annotations

from typing import List, Optional

from ape.fabric.contracts import AgentReport
from ape.fabric.memory import SharedMemoryWorkspace
from ape.fabric.registry import AgentRegistry, get_default_agent_registry


class AgentScheduler:
    """Orchestrates task assignment, sequential handoffs, and execution of Fabric Agents."""

    def __init__(self, registry: Optional[AgentRegistry] = None) -> None:
        self.registry = registry or get_default_agent_registry()
        self.execution_history: List[AgentReport] = []

    def schedule_sequence(
        self,
        roles_sequence: List[str],
        workspace_context: SharedMemoryWorkspace,
    ) -> List[AgentReport]:
        """Execute a sequence of Fabric Agents by role, passing shared memory context."""
        reports: List[AgentReport] = []

        for role in roles_sequence:
            agents = self.registry.get_agents_for_role(role)
            if not agents:
                # If no agent registered for role, record synthetic skip
                rep = AgentReport(
                    agent_name=f"auto_{role}",
                    role=role,
                    status="SKIPPED",
                    findings=[f"No specialized agent registered for role '{role}'"],
                )
                reports.append(rep)
                continue

            # Execute first available agent for role
            agent = agents[0]
            try:
                report = agent.execute(workspace_context)
                reports.append(report)
                self.execution_history.append(report)
                workspace_context.log_finding(report.agent_name, report.role, f"Execution completed with status {report.status}")
            except Exception as exc:
                err_report = AgentReport(
                    agent_name=getattr(agent, "name", "agent"),
                    role=role,
                    status="FAILED",
                    errors=[str(exc)],
                )
                reports.append(err_report)
                self.execution_history.append(err_report)

        return reports
