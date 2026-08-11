"""
Unit & Negative Security Tests for ORION-119.2 Governance Hardening Contracts.
Verifies 119.2.A (Swarm Governed Entry), 119.2.B (Live Lifecycle Revocation & Deprecated Observability Warning),
119.2.C (Context-Bound Scope Eligibility), and 119.2.D (Non-Blocking Evidence Subscriber).
"""

import json
import os
import tempfile

import pytest

from ape.capabilities import ExecutionContext
from ape.capabilities.broker import CapabilityBroker
from ape.capabilities.contracts import CapabilityError
from ape.capabilities.governance import (
    BindingType,
    CapabilityBinding,
    CapabilityDescriptor,
    CapabilityLifecycleState,
    CapabilityRegistry,
    CapabilityRequest,
)
from ape.capabilities.governance.evidence_subscriber import GovernanceEvidenceSubscriber
from ape.capabilities.governance.planner import GovernedExecutionPlanner
from ape.capabilities.governance.policy import CapabilityPolicyEvaluator
from ape.capabilities.governance.resolver import CapabilityBindingResolver
from ape.capabilities.integration.policy_gate import AuthorizationDecisionType
from ape.fabric.swarm import SwarmOrchestrator
from ape.tools.adapters.native import NativeToolAdapter, create_echo_tool
from ape.tools.definition import RiskLevel
from ape.tools.executor import ToolExecutor


def setup_119_2_environment():
    """Fixture establishing a 119.2 governed runtime environment."""
    registry = CapabilityRegistry()
    resolver = CapabilityBindingResolver()
    executor = ToolExecutor()

    echo_tool = create_echo_tool()
    adapter = NativeToolAdapter()
    adapter.register(echo_tool.definition, echo_tool.handler)
    executor.register_adapter(adapter)

    # 1. Workspace-scoped Echo Capability
    desc = CapabilityDescriptor(
        capability_id="test.hardened_echo",
        version="1.0.0",
        category="test",
        description="Hardened echo",
        risk_tier=RiskLevel.LOW,
    )
    bind = CapabilityBinding(
        binding_id="bind_hardened_echo",
        capability_id="test.hardened_echo",
        version="1.0.0",
        binding_type=BindingType.TOOL,
        target_id="echo",
        allowed_scopes=frozenset({"ws_permitted", "ws_staging"}),
    )
    registry.register(desc)
    resolver.register_binding(bind)

    planner = GovernedExecutionPlanner(
        capability_registry=registry,
        binding_resolver=resolver,
        tool_executor=executor,
    )

    broker = CapabilityBroker()
    broker.governance_registry = registry
    broker.binding_resolver = resolver
    broker.governed_planner = planner

    return registry, resolver, executor, planner, broker



def test_119_2_a_swarm_governed_entry():
    registry, resolver, executor, planner, broker = setup_119_2_environment()
    orchestrator = SwarmOrchestrator(capability_broker=broker)

    ctx = ExecutionContext(execution_id="ex_sw_01", venture_id="v1", trace_id="tr1", workspace_id="ws_permitted")

    # Execute swarm goal through Governed Capability entry
    outcome = orchestrator.execute_swarm_goal(
        goal="Run governed swarm pipeline",
        context=ctx,
        governed_capability_id="test.hardened_echo",
    )
    assert outcome is not None
    assert outcome.success is True


def test_119_2_b_in_flight_live_lifecycle_revoked_fails_closed():
    registry, resolver, executor, planner, broker = setup_119_2_environment()
    ctx = ExecutionContext(execution_id="ex_rev", venture_id="v1", trace_id="tr1", workspace_id="ws_permitted")

    req = CapabilityRequest(
        request_id="req_rev_01",
        capability_id="test.hardened_echo",
        input_payload={"message": "in flight test"},
        caller_identity="agent_01",
        context_id=ctx.execution_id,
        version_constraint="1.0.0",
    )

    # 1. Plan graph while ACTIVE
    graph = planner.plan_governed(req, ctx)
    node = graph.get_node("node_test.hardened_echo")

    # 2. Revoke capability live in registry after planning (in-flight state change)
    registry.set_lifecycle_state("test.hardened_echo@1.0.0", CapabilityLifecycleState.REVOKED)

    # 3. Executing node MUST fail closed live
    from ape.capabilities.contracts import ExecutionState, RuntimeContext
    state = ExecutionState(
        context=ctx,
        runtime=RuntimeContext(execution_id=ctx.execution_id, trace_id=ctx.trace_id),
        capability_id="test.hardened_echo",
        rendered_prompt=None,
    )
    with pytest.raises(CapabilityError) as exc_info:
        node.operation.execute(state)
    assert "FAIL CLOSED" in str(exc_info.value)
    assert "REVOKED" in str(exc_info.value)


def test_119_2_b_in_flight_live_lifecycle_deprecated_warning_only():
    registry, resolver, executor, planner, broker = setup_119_2_environment()
    ctx = ExecutionContext(execution_id="ex_dep", venture_id="v1", trace_id="tr1", workspace_id="ws_permitted")

    req = CapabilityRequest(
        request_id="req_dep_01",
        capability_id="test.hardened_echo",
        input_payload={"message": "deprecated test"},
        caller_identity="agent_01",
        context_id=ctx.execution_id,
        version_constraint="1.0.0",
    )

    # 1. Plan graph
    graph = planner.plan_governed(req, ctx)
    node = graph.get_node("node_test.hardened_echo")

    # 2. Mark DEPRECATED live in registry
    registry.set_lifecycle_state("test.hardened_echo@1.0.0", CapabilityLifecycleState.DEPRECATED)

    from ape.capabilities.contracts import ExecutionState, RuntimeContext
    state = ExecutionState(
        context=ctx,
        runtime=RuntimeContext(execution_id=ctx.execution_id, trace_id=ctx.trace_id),
        capability_id="test.hardened_echo",
        rendered_prompt=None,
    )
    # Execution MUST succeed and record warning event
    res_state = node.operation.execute(state)
    assert res_state is not None
    warning_events = [e for e in res_state.trace_events if e.event_type == "CapabilityDeprecatedWarning"]
    assert len(warning_events) == 1


def test_119_2_c_context_bound_scope_mismatch_denied():
    registry, resolver, executor, planner, broker = setup_119_2_environment()

    desc = registry.resolve_version("test.hardened_echo", "1.0.0")
    bind = resolver.resolve_binding(desc)

    # Context with unauthorized workspace
    bad_ctx = ExecutionContext(execution_id="ex_bad_ws", venture_id="v1", trace_id="tr1", workspace_id="ws_UNAUTHORIZED")

    # Evaluate effective authorization
    decision = CapabilityPolicyEvaluator.evaluate_effective_authorization(
        request_id="req_scope_01",
        descriptor=desc,
        binding=bind,
        context=bad_ctx,
        call_id="call_scope_01",
    )

    assert decision.decision == AuthorizationDecisionType.DENY
    assert "SCOPE_MISMATCH" in decision.reason


def test_119_2_d_non_blocking_evidence_subscriber():
    with tempfile.TemporaryDirectory() as tmp_dir:
        registry, resolver, executor, planner, broker = setup_119_2_environment()

        # Attach subscriber to broker's event_bus
        subscriber = GovernanceEvidenceSubscriber(evidence_dir=tmp_dir)
        subscriber.attach_to_event_bus(broker.event_bus)

        ctx = ExecutionContext(execution_id="ex_ev_01", venture_id="v1", trace_id="tr1", workspace_id="ws_permitted")
        req = CapabilityRequest(
            request_id="req_ev_01",
            capability_id="test.hardened_echo",
            input_payload={"message": "evidence test"},
            caller_identity="agent_01",
            context_id=ctx.execution_id,
            version_constraint="1.0.0",
        )

        res = broker.execute_capability(req, ctx, governed_planner=planner)
        assert res.final().success is True

        # Check JSONL evidence file written
        files = os.listdir(tmp_dir)
        assert len(files) > 0
        dec_file = [f for f in files if f.startswith("decisions-") or f.startswith("execution-")][0]
        with open(os.path.join(tmp_dir, dec_file), "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) > 0
            event_data = json.loads(lines[0])
            assert "event_type" in event_data
