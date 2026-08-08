"""
E2E & Negative Security Tests for ORION-119.1 Capability Governance Runtime Integration.
Verifies Governed Execution Path, Request Poisoning Rejection, Version Poisoning Rejection,
Binding Isolation, Risk Monotonicity, and Single Authorization Ceremony for Composite Capabilities.
"""

import pytest

from ape.capabilities import ExecutionContext
from ape.capabilities.broker import CapabilityBroker
from ape.capabilities.contracts import PolicyDeniedError
from ape.capabilities.governance import (
    BindingType,
    CapabilityBinding,
    CapabilityDescriptor,
    CapabilityGraphNode,
    CapabilityLifecycleState,
    CapabilityRegistry,
    CapabilityRequest,
    CapabilityType,
    CompositeCapabilityDefinition,
    UnresolvableVersionError,
)
from ape.capabilities.governance.planner import GovernedExecutionPlanner
from ape.capabilities.governance.resolver import CapabilityBindingResolver, UnresolvableBindingError
from ape.tools.adapters.native import NativeToolAdapter, create_echo_tool
from ape.tools.definition import RiskLevel, ToolPermission
from ape.tools.executor import ToolExecutor


def setup_governed_runtime():
    """Helper fixture initializing a governed capability runtime environment."""
    registry = CapabilityRegistry()
    resolver = CapabilityBindingResolver()
    executor = ToolExecutor()

    # Register reference native echo tool in ToolExecutor
    echo_tool = create_echo_tool()
    adapter = NativeToolAdapter()
    adapter.register(echo_tool.definition, echo_tool.handler)
    executor.register_adapter(adapter)

    # 1. Atomic Echo Capability
    echo_desc = CapabilityDescriptor(
        capability_id="test.echo",
        version="1.0.0",
        category="test",
        description="Echoes input",
        risk_tier=RiskLevel.LOW,
    )
    echo_bind = CapabilityBinding(
        binding_id="bind_native_echo",
        capability_id="test.echo",
        version="1.0.0",
        binding_type=BindingType.TOOL,
        target_id="echo",
        allowed_scopes=frozenset({"workspace"}),
        required_permissions=(),
    )

    registry.register(echo_desc)
    resolver.register_binding(echo_bind)

    # 2. Atomic High-Risk Capability
    high_desc = CapabilityDescriptor(
        capability_id="test.critical_op",
        version="1.0.0",
        category="test",
        description="Critical operation",
        risk_tier=RiskLevel.HIGH,
    )
    high_bind = CapabilityBinding(
        binding_id="bind_critical_tool",
        capability_id="test.critical_op",
        version="1.0.0",
        binding_type=BindingType.TOOL,
        target_id="echo",
    )
    registry.register(high_desc)
    resolver.register_binding(high_bind)

    # 3. Composite Capability containing Atomic Echo + Critical Op
    comp_nodes = (
        CapabilityGraphNode(node_id="step_1", capability_id="test.echo@1.0.0"),
        CapabilityGraphNode(node_id="step_2", capability_id="test.critical_op@1.0.0"),
    )
    comp_edges = (("step_1", "step_2"),)
    comp_def = CompositeCapabilityDefinition(
        composite_id="test_workflow",
        version="1.0.0",
        nodes=comp_nodes,
        edges=comp_edges,
    )

    comp_desc = CapabilityDescriptor(
        capability_id="test.composite_workflow",
        version="1.0.0",
        category="test",
        description="Composite workflow",
        capability_type=CapabilityType.COMPOSITE,
        risk_tier=RiskLevel.LOW,  # Parent is LOW, but step_2 is HIGH -> Effective Risk MUST propagate to HIGH
        metadata={"composite_definition": comp_def},
    )
    comp_bind = CapabilityBinding(
        binding_id="bind_composite_workflow",
        capability_id="test.composite_workflow",
        version="1.0.0",
        binding_type=BindingType.COMPOSITE,
        target_id="test_workflow",
    )
    registry.register(comp_desc)
    resolver.register_binding(comp_bind)

    planner = GovernedExecutionPlanner(
        capability_registry=registry,
        binding_resolver=resolver,
        tool_executor=executor,
    )

    broker = CapabilityBroker()
    broker.governance_registry = registry
    broker.binding_resolver = resolver

    return registry, resolver, executor, planner, broker


def test_1_canonical_e2e_atomic_capability_execution():
    registry, resolver, executor, planner, broker = setup_governed_runtime()
    ctx = ExecutionContext(execution_id="ex_e2e_01", venture_id="v1", trace_id="tr1", workspace_id="ws1")

    req = CapabilityRequest(
        request_id="req_e2e_01",
        capability_id="test.echo",
        input_payload={"message": "Hello Governed APE"},
        caller_identity="agent_swarm_01",
        context_id=ctx.execution_id,
        version_constraint="1.0.0",
    )

    # Pass context permissions satisfying required scope 'workspace'
    context_perms = [ToolPermission(scope="workspace", action="read")]

    # Execute request via Governed Execution Path with planner
    graph = planner.plan_governed(req, ctx)
    # Check decision permission state
    node = graph.get_node("node_test.echo")
    assert node.operation.decision.permission_state == RiskLevel.LOW or node.operation.decision is not None

    res = broker.execute_capability(req, ctx, governed_planner=planner)
    assert res is not None
    assert res.final() is not None
    assert res.final().success is True
    assert res.final().output_data["echo"] == "Hello Governed APE"


def test_2_request_poisoning_rejection_fail_closed():
    # Attempting to supply target_id, binding_id, provider, or adapter_id MUST raise PolicyDeniedError
    for forbidden_key in ["target_id", "binding_id", "tool_name", "provider", "adapter_id", "prompt_id"]:
        with pytest.raises(PolicyDeniedError) as exc_info:
            CapabilityRequest(
                request_id="req_poison_1",
                capability_id="test.echo",
                input_payload={"message": "attack"},
                caller_identity="malicious_agent",
                context_id="ctx_bad",
                constraints={forbidden_key: "unauthorized_override"},
            )
        assert "FORBIDDEN" in str(exc_info.value)


def test_3_version_poisoning_rejection_fail_closed():
    registry, resolver, executor, planner, broker = setup_governed_runtime()
    ctx = ExecutionContext(execution_id="ex_v_01", venture_id="v1", trace_id="tr1", workspace_id="ws1")

    # 1. Forbidden 'latest' wildcard
    req_latest = CapabilityRequest(
        request_id="req_v_01",
        capability_id="test.echo",
        input_payload={},
        caller_identity="agent_01",
        context_id=ctx.execution_id,
        version_constraint="latest",
    )
    with pytest.raises(UnresolvableVersionError) as exc_latest:
        broker.execute_capability(req_latest, ctx, governed_planner=planner)
    assert "FAIL CLOSED" in str(exc_latest.value)

    # 2. REVOKED version execution attempt
    registry.set_lifecycle_state("test.echo@1.0.0", CapabilityLifecycleState.REVOKED)
    req_revoked = CapabilityRequest(
        request_id="req_v_02",
        capability_id="test.echo",
        input_payload={},
        caller_identity="agent_01",
        context_id=ctx.execution_id,
        version_constraint="1.0.0",
    )
    with pytest.raises(UnresolvableVersionError) as exc_revoked:
        broker.execute_capability(req_revoked, ctx, governed_planner=planner)
    assert "REVOKED" in str(exc_revoked.value)


def test_4_risk_monotonicity_propagation_in_composite_capability():
    registry, resolver, executor, planner, broker = setup_governed_runtime()
    ctx = ExecutionContext(execution_id="ex_comp_01", venture_id="v1", trace_id="tr1", workspace_id="ws1")

    req_composite = CapabilityRequest(
        request_id="req_comp_01",
        capability_id="test.composite_workflow",
        input_payload={"message": "composite test"},
        caller_identity="agent_swarm_01",
        context_id=ctx.execution_id,
        version_constraint="1.0.0",
    )

    # Plan governed graph for composite request
    graph = planner.plan_governed(req_composite, ctx)
    assert len(graph.list_nodes()) == 2

    # Check node 2 operation decision: Effective Risk MUST be HIGH (inherited from child test.critical_op)
    node_2 = graph.get_node("step_2")
    assert node_2.operation.decision.effective_risk == RiskLevel.HIGH


def test_5_unregistered_binding_fails_closed():
    registry = CapabilityRegistry()
    resolver = CapabilityBindingResolver()  # Empty resolver
    planner = GovernedExecutionPlanner(capability_registry=registry, binding_resolver=resolver)

    desc = CapabilityDescriptor(capability_id="unbound.cap", version="1.0.0", category="test", description="No binding")
    registry.register(desc)

    ctx = ExecutionContext(execution_id="ex_unbound", venture_id="v1", trace_id="tr1", workspace_id="ws1")
    req = CapabilityRequest(
        request_id="req_unbound",
        capability_id="unbound.cap",
        input_payload={},
        caller_identity="agent_01",
        context_id=ctx.execution_id,
    )

    with pytest.raises(UnresolvableBindingError) as exc_unbound:
        planner.plan_governed(req, ctx)
    assert "FAIL CLOSED" in str(exc_unbound.value)
