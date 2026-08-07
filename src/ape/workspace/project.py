"""
Project Graph Topology — RFC-022 / PR-W2 Specification.
Models hierarchical project nodes (Backend, Frontend, Mobile, Infra, Docs) within workspaces.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProjectNode:
    """Represents a project node within a workspace topology graph."""
    name: str
    project_type: str  # backend, frontend, mobile, infra, docs
    path: str
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "project_type": self.project_type,
            "path": self.path,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
        }


class ProjectTopology:
    """Manages hierarchical project graph topologies within a workspace."""

    def __init__(self, workspace_name: str) -> None:
        self.workspace_name = workspace_name
        self.nodes: Dict[str, ProjectNode] = {}

    def add_project(self, name: str, project_type: str, path: str, dependencies: Optional[List[str]] = None) -> ProjectNode:
        """Add or update a project node in topology graph."""
        key = name.strip().lower()
        node = ProjectNode(
            name=name,
            project_type=project_type,
            path=path,
            dependencies=dependencies or [],
        )
        self.nodes[key] = node
        return node

    def get_project(self, name: str) -> Optional[ProjectNode]:
        """Fetch project node by name."""
        return self.nodes.get(name.strip().lower())

    def get_topological_order(self) -> List[ProjectNode]:
        """Return topological execution order of projects resolving internal dependencies."""
        visited: set[str] = set()
        order: List[ProjectNode] = []

        def dfs(node_key: str):
            if node_key in visited:
                return
            visited.add(node_key)
            node = self.nodes.get(node_key)
            if node:
                for dep in node.dependencies:
                    dep_key = dep.strip().lower()
                    if dep_key in self.nodes:
                        dfs(dep_key)
                order.append(node)

        for k in self.nodes:
            dfs(k)

        return order

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workspace_name": self.workspace_name,
            "projects_count": len(self.nodes),
            "projects": {k: v.to_dict() for k, v in self.nodes.items()},
        }
