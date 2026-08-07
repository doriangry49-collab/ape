"""
Topic & Inter-Project DAG Execution Engine — RFC-022 / PR-W3 & PR-W4 Specification.
Topologically sorts and executes topic lifecycle graphs (Research -> Architecture -> Implementation -> QA -> Release).
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class TopicNode:
    """Represents a topic node in a DAG execution graph."""
    topic_slug: str
    stage_name: str
    dependencies: List[str] = field(default_factory=list)
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic_slug": self.topic_slug,
            "stage_name": self.stage_name,
            "dependencies": self.dependencies,
            "status": self.status,
        }


class TopicDAGEngine:
    """Orchestrates topic lifecycle DAGs and inter-project build triggers."""

    def __init__(self) -> None:
        self.nodes: Dict[str, TopicNode] = {}

    def add_topic_stage(self, topic_slug: str, stage_name: str, dependencies: Optional[List[str]] = None) -> TopicNode:
        """Add a stage node to topic DAG."""
        key = f"{topic_slug}:{stage_name}".lower()
        node = TopicNode(
            topic_slug=topic_slug,
            stage_name=stage_name,
            dependencies=dependencies or [],
        )
        self.nodes[key] = node
        return node

    def get_execution_order(self) -> List[TopicNode]:
        """Return topological execution sequence of DAG nodes."""
        visited: set[str] = set()
        order: List[TopicNode] = []

        def dfs(node_key: str):
            if node_key in visited:
                return
            visited.add(node_key)
            node = self.nodes.get(node_key)
            if node:
                for dep in node.dependencies:
                    dep_key = dep.lower()
                    if dep_key in self.nodes:
                        dfs(dep_key)
                order.append(node)

        for k in self.nodes:
            dfs(k)

        return order

    def execute_dag(self, executor_fn: Optional[Callable[[TopicNode], bool]] = None) -> Dict[str, Any]:
        """Execute all nodes in DAG following topological order."""
        seq = self.get_execution_order()
        results: Dict[str, str] = {}

        for node in seq:
            node.status = "RUNNING"
            success = executor_fn(node) if executor_fn else True
            node.status = "COMPLETED" if success else "FAILED"
            results[f"{node.topic_slug}:{node.stage_name}"] = node.status

            if not success:
                break

        return {
            "nodes_executed": len(results),
            "results": results,
        }
