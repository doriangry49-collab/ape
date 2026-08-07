"""
ExecutionPlanner Specification — ORION-115.
Defines ExecutionPlanner Protocol and StandardExecutionPlanner converting ExecutionRequest into ExecutionGraph.
"""

from typing import Any, Protocol, runtime_checkable

from ape.capabilities.graph import ExecutionGraph, ExecutionNode
from ape.capabilities.operation import ProviderOperation
from ape.capabilities.pipeline import (
    AdapterExecutionStage,
    PolicyEnforcementStage,
    ResolveCandidateStage,
    StrategySelectionStage,
)
from ape.capabilities.request import ExecutionRequest


@runtime_checkable
class ExecutionPlanner(Protocol):
    """Planner Protocol building ExecutionGraph topology from ExecutionRequest contract."""
    planner_name: str

    def plan(self, request: ExecutionRequest, capability_matrix: Any, capability_registry: Any, circuit_breaker: Any) -> ExecutionGraph:
        ...


class StandardExecutionPlanner:
    """Standard planner creating execution graph for capability requests."""
    planner_name: str = "STANDARD_PLANNER"

    def plan(self, request: ExecutionRequest, capability_matrix: Any, capability_registry: Any, circuit_breaker: Any) -> ExecutionGraph:
        graph = ExecutionGraph(graph_id=f"graph_{request.request_id}")

        n_resolve = ExecutionNode("resolve", ResolveCandidateStage(capability_matrix, capability_registry))
        n_policy = ExecutionNode("policy", PolicyEnforcementStage(circuit_breaker, request.policy), dependencies=["resolve"])
        n_strategy = ExecutionNode("strategy", StrategySelectionStage(), dependencies=["policy"])
        n_adapter = ExecutionNode("adapter", AdapterExecutionStage(), dependencies=["strategy"])

        graph.add_node(n_resolve)
        graph.add_node(n_policy)
        graph.add_node(n_strategy)
        graph.add_node(n_adapter)

        graph.add_edge("resolve", "policy")
        graph.add_edge("policy", "strategy")
        graph.add_edge("strategy", "adapter")

        return graph
