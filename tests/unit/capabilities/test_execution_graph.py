"""
Unit tests for ORION-115 Execution Graph Runtime.
Verifies pure data structure ExecutionGraph (nodes, edges, topological sort, cycle detection),
ExecutionPlanner graph generation, ExecutionScheduler decoupling, ExecutionOperation compensation,
ExecutionEventStore event sourcing & MemorySnapshot materialization, ProviderEvaluation calculators,
and pure facade CapabilityBroker.
"""

import pytest

from ape.capabilities import (
    BalancedCalculator,
    CapabilityBroker,
    CapabilityMatrix,
    CapabilityRegistry,
    CostFirstCalculator,
    EnterpriseCalculator,
    ExecutionArtifact,
    ExecutionContext,
    ExecutionEdge,
    ExecutionEngine,
    ExecutionEventStore,
    ExecutionGraph,
    ExecutionMode,
    ExecutionNode,
    ExecutionPlanner,
    ExecutionRequest,
    ExecutionResult,
    ExecutionTraceBuilder,
    FileOperation,
    LatencyFirstCalculator,
    MockProviderAdapter,
    ProviderEvaluation,
    ProviderOperation,
    ProviderRegistry,
    SequentialScheduler,
    StandardExecutionPlanner,
    StateEvent,
    ToolCall,
    ToolOperation,
)
from ape.prompts import RenderedPrompt


@pytest.fixture
def sample_prompt() -> RenderedPrompt:
    return RenderedPrompt(
        system_prompt="You are an AI Operating System Kernel.",
        user_prompt="Run ExecutionGraph DAG tests.",
        prompt_id="engineering.nextjs_blueprint",
        version="1.0.0",
        template_sha256="sha_tmpl_115",
        rendered_sha256="sha_rnd_115",
        trace_id="trc_graph_115",
    )


@pytest.fixture
def sample_context() -> ExecutionContext:
    return ExecutionContext(
        execution_id="ex_graph_115",
        venture_id="v_graph_115",
        trace_id="trc_graph_115",
        workspace_id="ws_graph_115",
    )


def test_execution_graph_dag_topology():
    graph = ExecutionGraph("test_dag")
    n1 = ExecutionNode("n1", "op1")
    n2 = ExecutionNode("n2", "op2", dependencies=["n1"])
    n3 = ExecutionNode("n3", "op3", dependencies=["n2"])

    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)

    graph.add_edge("n1", "n2")
    graph.add_edge("n2", "n3")

    assert graph.has_cycle() is False
    sorted_nodes = graph.topological_sort()
    assert [n.node_id for n in sorted_nodes] == ["n1", "n2", "n3"]


def test_execution_graph_cycle_detection():
    graph = ExecutionGraph("cycle_dag")
    n1 = ExecutionNode("n1", "op1")
    n2 = ExecutionNode("n2", "op2")

    graph.add_node(n1)
    graph.add_node(n2)

    graph.add_edge("n1", "n2")
    graph.add_edge("n2", "n1")

    assert graph.has_cycle() is True
    with pytest.raises(ValueError, match="contains cycles"):
        graph.topological_sort()


def test_execution_planner_and_scheduler(sample_prompt, sample_context):
    req = ExecutionRequest(
        request_id="req_115",
        capability_id="engineering.code.generate",
        rendered_prompt=sample_prompt,
        context=sample_context,
        mode=ExecutionMode.SYNC,
    )

    cap_reg = CapabilityRegistry()
    prov_reg = ProviderRegistry()
    matrix = CapabilityMatrix(prov_reg)

    planner = StandardExecutionPlanner()
    graph = planner.plan(req, matrix, cap_reg, None)

    assert isinstance(graph, ExecutionGraph)
    assert graph.has_cycle() is False
    assert len(graph.list_nodes()) == 4

    scheduler = SequentialScheduler()
    engine = ExecutionEngine()

    res = scheduler.schedule(graph, req, engine)
    assert isinstance(res, ExecutionResult)
    assert res.final().success is True


def test_execution_operation_compensation(sample_context):
    tool_call = ToolCall("c1", "deploy_app", {"env": "prod"})
    op_tool = ToolOperation(tool_call)

    class DummyState:
        working_memory = {}

    state = DummyState()
    op_tool.execute(state)
    assert state.working_memory["tool_deploy_app"] == "Executed"

    op_tool.compensate(state)
    assert state.working_memory["tool_deploy_app"] == "Compensated"


def test_execution_event_store_and_memory_snapshot():
    store = ExecutionEventStore("trc_115")
    store.append("user_name", "Aria")
    store.append("budget_limit", 100.0)

    snapshot = store.materialize()
    assert snapshot.get("user_name") == "Aria"
    assert snapshot.get("budget_limit") == 100.0
    assert snapshot.event_count == 2


def test_provider_evaluation_calculators(sample_context):
    p_smart = MockProviderAdapter("smart-llm", cost_per_1k_tokens=0.005)

    cost_calc = CostFirstCalculator()
    eval_cost = cost_calc.calculate_evaluation(p_smart, sample_context)
    assert isinstance(eval_cost, ProviderEvaluation)
    assert "cost" in eval_cost.weights

    ent_calc = EnterpriseCalculator()
    eval_ent = ent_calc.calculate_evaluation(p_smart, sample_context)
    assert eval_ent.score >= 70.0


def test_capability_broker_pure_facade(sample_prompt, sample_context):
    broker = CapabilityBroker()
    req = ExecutionRequest(
        request_id="req_facade",
        capability_id="engineering.code.generate",
        rendered_prompt=sample_prompt,
        context=sample_context,
    )

    res = broker.execute_request(req)
    assert isinstance(res, ExecutionResult)
    assert res.final().success is True
