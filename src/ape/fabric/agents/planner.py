"""
Planner Agent Reference Implementation — RFC-022 / PR-A6 Specification.
Decomposes user topic into strategic execution tasks and registers execution plan in shared memory.
"""

from typing import Any

from ape.fabric.contracts import AgentReport
from ape.fabric.memory import SharedMemoryWorkspace


class PlannerAgent:
    """Specialized Fabric Agent for research decomposition and task graph planning."""

    role = "planner"
    capabilities = ["roadmap_planning", "task_graph_decomposition"]

    @property
    def name(self) -> str:
        return "ape_planner_agent"

    def execute(self, workspace_context: SharedMemoryWorkspace) -> AgentReport:
        topic = workspace_context.topic_slug
        tasks = [
            {"id": "t1", "description": f"Research baseline architecture for {topic}"},
            {"id": "t2", "description": f"Generate core implementation files for {topic}"},
            {"id": "t3", "description": "Audit quality and execute test verification"},
        ]
        workspace_context.set("execution_plan", tasks)
        workspace_context.log_finding(self.name, self.role, f"Decomposed topic '{topic}' into {len(tasks)} tasks.")

        return AgentReport(
            agent_name=self.name,
            role=self.role,
            status="COMPLETED",
            outputs={"tasks_count": len(tasks)},
            findings=[f"Decomposed '{topic}' into 3 tasks"],
        )

    def explain(self) -> str:
        return "PlannerAgent analyzes topics and constructs execution plans for downstream agents."

    def observe(self, event: Any) -> None:
        pass

    def report(self) -> AgentReport:
        return AgentReport(agent_name=self.name, role=self.role, status="COMPLETED")
