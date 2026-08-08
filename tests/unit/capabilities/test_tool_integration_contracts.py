"""
Unit tests for ORION-118 Tool Integration Contracts.
Verifies CapabilityToolResolver, ToolCandidate, ToolResultExecutionMapper, EffectivePolicyGate,
3-tier permission state taxonomy, and spoof-proof AuthorizationDecision binding.
"""

from typing import Any, Dict, Optional
import pytest

from ape.capabilities import ExecutionContext, ExecutionPolicy
from ape.capabilities.integration import (
    AuthorizationDecision,
    AuthorizationDecisionType,
    CapabilityToolResolver,
    EffectivePolicyGate,
    PermissionState,
    ResolutionResult,
    ToolCandidate,
    ToolExecutionEvent,
    ToolResultExecutionMapper,
)
from ape.tools import (
    RiskLevel,
    ToolDefinition,
    ToolPermission,
    ToolRegistry,
    ToolResult,
    ToolScope,
)


class MockCapabilityToolResolver(CapabilityToolResolver):
    """Mock implementation of CapabilityToolResolver for contract testing."""

    def resolve_tool_for_capability(
        self,
        capability_id: str,
        registry: ToolRegistry,
        context: ExecutionContext,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> ResolutionResult:
        tool_def = registry.resolve_tool("structured_transform")
        candidate = ToolCandidate(
            tool_definition=tool_def,
            adapter_id="native_adapter",
            locality="native",
            registry_scope=ToolScope.GLOBAL,
            estimated_cost=0.001,
        )
        return ResolutionResult(
            capability_id=capability_id,
            selected_candidate=candidate,
            resolution_strategy="lowest_cost",
            candidate_count=1,
        )


def test_tool_candidate_and_resolution_result():
    tool_def = ToolDefinition(name="echo", version="1.0.0", description="Echo tool")
    candidate = ToolCandidate(
        tool_definition=tool_def,
        adapter_id="native_adapter",
        locality="native",
        registry_scope=ToolScope.GLOBAL,
    )

    assert candidate.adapter_id == "native_adapter"
    assert candidate.registry_scope == ToolScope.GLOBAL

    res = ResolutionResult(
        capability_id="data.echo",
        selected_candidate=candidate,
        resolution_strategy="pinned",
        candidate_count=1,
    )

    assert res.capability_id == "data.echo"
    assert res.selected_candidate.tool_definition.name == "echo"


def test_capability_tool_resolver_execution():
    registry = ToolRegistry()
    tool_def = ToolDefinition(name="structured_transform", version="1.0.0", description="Transform tool")
    registry.register_tool(tool_def)

    resolver = MockCapabilityToolResolver()
    ctx = ExecutionContext(execution_id="exec_100", venture_id="v1", trace_id="tr1", workspace_id="ws1")

    res = resolver.resolve_tool_for_capability("data.transform", registry, ctx)
    assert res.selected_candidate.tool_definition.name == "structured_transform"
    assert res.selected_candidate.adapter_id == "native_adapter"


def test_pure_tool_result_execution_mapper():
    raw_result = ToolResult(
        call_id="call_999",
        tool_name="deterministic_compute",
        success=True,
        output_data={"hash": "abcdef1234567890"},
        evidence_hash="ev_hash_123",
        duration_ms=12.5,
    )

    event = ToolResultExecutionMapper.map_to_event(raw_result, event_id="evt_001")

    assert isinstance(event, ToolExecutionEvent)
    assert event.event_id == "evt_001"
    assert event.call_id == "call_999"
    assert event.success is True
    assert event.evidence_hash == "ev_hash_123"
    # Verify no state mutation side-effects occurred in mapper
    assert raw_result.call_id == "call_999"


def test_effective_policy_gate_taxonomy_and_decision():
    policy = ExecutionPolicy()
    ctx = ExecutionContext(execution_id="exec_sec_1", venture_id="v1", trace_id="tr1", workspace_id="ws1")

    tool_low = ToolDefinition(
        name="low_risk_tool",
        version="1.0.0",
        description="Low risk tool",
        permissions=[ToolPermission(scope="workspace", action="read")],
        risk_level=RiskLevel.LOW,
    )

    # 1. Satisfied Permissions & Low Risk -> ALLOW
    decision_allow = EffectivePolicyGate.evaluate(
        capability_policy=policy,
        tool_definition=tool_low,
        context=ctx,
        call_id="call_allow_1",
        capability_id="storage.read",
        context_permissions=[ToolPermission(scope="workspace", action="read")],
    )

    assert decision_allow.decision == AuthorizationDecisionType.ALLOW
    assert decision_allow.permission_state == PermissionState.SATISFIED
    assert decision_allow.verify_binding("call_allow_1", "storage.read", "low_risk_tool", "exec_sec_1") is True

    # 2. Missing Grantable Permission -> REQUIRE_APPROVAL
    tool_grantable = ToolDefinition(
        name="grantable_tool",
        version="1.0.0",
        description="Requires grantable scope",
        permissions=[ToolPermission(scope="workspace", action="write")],
        risk_level=RiskLevel.LOW,
    )

    decision_req = EffectivePolicyGate.evaluate(
        capability_policy=policy,
        tool_definition=tool_grantable,
        context=ctx,
        call_id="call_req_1",
        capability_id="storage.write",
        grantable_scopes={"workspace"},
        approved_by_human=False,
    )

    assert decision_req.decision == AuthorizationDecisionType.REQUIRE_APPROVAL
    assert decision_req.permission_state == PermissionState.MISSING_BUT_GRANTABLE

    # 3. Forbidden Scope -> DENY
    tool_forbidden = ToolDefinition(
        name="forbidden_tool",
        version="1.0.0",
        description="Requires ungrantable system scope",
        permissions=[ToolPermission(scope="kernel:root", action="admin")],
        risk_level=RiskLevel.CRITICAL,
    )

    decision_deny = EffectivePolicyGate.evaluate(
        capability_policy=policy,
        tool_definition=tool_forbidden,
        context=ctx,
        call_id="call_deny_1",
        capability_id="kernel.admin",
        grantable_scopes={"workspace"},
    )

    assert decision_deny.decision == AuthorizationDecisionType.DENY
    assert decision_deny.permission_state == PermissionState.FORBIDDEN


def test_authorization_decision_binding_spoofing_protection():
    ctx = ExecutionContext(execution_id="exec_spoof_1", venture_id="v1", trace_id="tr1", workspace_id="ws1")
    policy = ExecutionPolicy()
    tool_def = ToolDefinition(name="calculate_hash", version="1.0.0", description="Hash tool", risk_level=RiskLevel.LOW)

    decision = EffectivePolicyGate.evaluate(
        capability_policy=policy,
        tool_definition=tool_def,
        context=ctx,
        call_id="valid_call_10",
        capability_id="compute.hash",
    )

    # Valid matching binding check -> True
    assert decision.verify_binding("valid_call_10", "compute.hash", "calculate_hash", "exec_spoof_1") is True

    # Spoofed call_id or tool_id binding check -> False
    assert decision.verify_binding("spoofed_call_99", "compute.hash", "calculate_hash", "exec_spoof_1") is False
    assert decision.verify_binding("valid_call_10", "compute.hash", "other_tool", "exec_spoof_1") is False
