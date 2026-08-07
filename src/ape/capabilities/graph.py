"""
ExecutionGraph & DAG Topology Specification — ORION-115 Specification.
Defines ExecutionNode, ExecutionEdge, and pure data structure ExecutionGraph with topological sorting and cycle detection.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class ExecutionNode:
    """DAG node representing an execution operation or stage."""
    node_id: str
    operation: Any
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionEdge:
    """DAG edge representing dependency relationship between target and source nodes."""
    source_id: str
    target_id: str
    edge_type: str = "dependency"


class ExecutionGraph:
    """Pure data structure representing a Directed Acyclic Graph (DAG) of execution nodes and edges."""

    def __init__(self, graph_id: str = "graph_default") -> None:
        self.graph_id = graph_id
        self._nodes: Dict[str, ExecutionNode] = {}
        self._edges: List[ExecutionEdge] = []

    def add_node(self, node: ExecutionNode) -> None:
        """Add a node to graph topology."""
        self._nodes[node.node_id] = node

    def add_edge(self, source_id: str, target_id: str, edge_type: str = "dependency") -> None:
        """Add a directed edge from source_id to target_id."""
        if source_id not in self._nodes or target_id not in self._nodes:
            raise ValueError(f"Cannot add edge between '{source_id}' and '{target_id}'; nodes must be registered first.")

        edge = ExecutionEdge(source_id=source_id, target_id=target_id, edge_type=edge_type)
        self._edges.append(edge)

        if source_id not in self._nodes[target_id].dependencies:
            self._nodes[target_id].dependencies.append(source_id)

    def get_node(self, node_id: str) -> ExecutionNode:
        if node_id not in self._nodes:
            raise KeyError(f"Node '{node_id}' is not registered in ExecutionGraph '{self.graph_id}'.")
        return self._nodes[node_id]

    def list_nodes(self) -> List[ExecutionNode]:
        return list(self._nodes.values())

    def has_cycle(self) -> bool:
        """Check if graph topology contains cycles using Kahn's algorithm."""
        in_degree: Dict[str, int] = {node_id: len(node.dependencies) for node_id, node in self._nodes.items()}
        queue = [node_id for node_id, deg in in_degree.items() if deg == 0]
        visited_count = 0

        # Adjacency list
        adj: Dict[str, List[str]] = {node_id: [] for node_id in self._nodes}
        for edge in self._edges:
            adj[edge.source_id].append(edge.target_id)

        while queue:
            curr = queue.pop(0)
            visited_count += 1

            for nxt in adj[curr]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)

        return visited_count != len(self._nodes)

    def topological_sort(self) -> List[ExecutionNode]:
        """Return nodes in valid topological execution order."""
        if self.has_cycle():
            raise ValueError(f"ExecutionGraph '{self.graph_id}' contains cycles and cannot be topologically sorted.")

        in_degree: Dict[str, int] = {node_id: len(node.dependencies) for node_id, node in self._nodes.items()}
        queue = [node_id for node_id, deg in in_degree.items() if deg == 0]
        result: List[ExecutionNode] = []

        adj: Dict[str, List[str]] = {node_id: [] for node_id in self._nodes}
        for edge in self._edges:
            adj[edge.source_id].append(edge.target_id)

        while queue:
            curr = queue.pop(0)
            result.append(self._nodes[curr])

            for nxt in adj[curr]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)

        return result
