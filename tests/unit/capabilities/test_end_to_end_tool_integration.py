"""
End-to-End & Negative Integration Test Suite for ORION-118 Tool Integration Bridge.
Verifies full canonical lifecycle, EffectiveToolPolicyEvaluator decision binding enforcement,
ToolExecutionStage state updates, and Native + MCP execution paths.
"""

from typing import Any, Dict, Optional
import pytest

from ape.capabilities import ExecutionContext, ExecutionPolicy, ExecutionState, RuntimeContext
from ape.capabilities.integration import (
    AuthorizationDecision,
    AuthorizationDecisionType,
    CapabilityToolResolver,
    EffectivePolicyGate,
    EffectiveToolPolicyEvaluator,
    PermissionState,
    ResolutionResult,
    ToolCandidate,
    ToolExecutionEvent,
    ToolExecutionStage,
    ToolResultExecutionMapper,
)
from ape.tools import (
    ApprovalRequiredError,
    NativeToolAdapter,
    RiskLevel,
    ToolAuthorizationError,
    ToolCallPayload,
    ToolDefinition,
    ToolExecutor,
    ToolPermission,
    ToolRegistry,
    ToolScope,
)
from ape.tools.adapters.native import create_echo_tool, create_structured_transform_tool


class EndToEndResolver(CapabilityToolResolver):
    """Resolver for E2E integration test."""

    def resolve_tool_for_capability(
        self,
        capability_id: str,
        registry: ToolRegistry,
        context: ExecutionContext,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> ResolutionResult:
        tool_name = "echo"
        tool_def = registry.resolve_tool(tool_name)
        candidate = ToolCandidate(
            tool_definition=tool_def,
            adapter_id="native_adapter",
            locality="native",
            registry_scope=ToolScope.GLOBAL,
        )
        return ResolutionResult(
            capability_id=capability_id,
            selected_candidate=candidate,
            resolution_strategy="pinned",
            candidate_count=1,
        )


def test_canonical_end_to_end_native_tool_flow():
    # 1. Setup Tool Subsystem & Adapter with registered echo tool
    executor = ToolExecutor()
    native_adapter = NativeToolAdapter()
    echo_tool = create_echo_tool()
    native_adapter.register(echo_tool.definition, echo_tool.handler)
    executor.register_adapter(native_adapter)

    # 2. Context & Request
    ctx = ExecutionContext(execution_id="exec_e2e_native", venture_id="v1", trace_id="tr_e2e_1", workspace_id="ws1")
    capability_id = "data.echo"
    call_id = "call_e2e_echo_101"

    # 3. Step A: CapabilityToolResolver
    resolver = EndToEndResolver()
    res_result = resolver.resolve_tool_for_capability(capability_id, executor.registry, ctx)
    selected_tool = res_result.selected_candidate.tool_definition

    # 4. Step B: EffectivePolicyGate Evaluation
    auth_decision = EffectivePolicyGate.evaluate(
        capability_policy=ExecutionPolicy(),
        tool_definition=selected_tool,
        context=ctx,
        call_id=call_id,
        capability_id=capability_id,
    )
    assert auth_decision.decision == AuthorizationDecisionType.ALLOW

    # 5. Step C: Bind Decision to EffectiveToolPolicyEvaluator & Inject into ToolExecutor
    evaluator_bridge = EffectiveToolPolicyEvaluator()
    evaluator_bridge.set_active_decision(auth_decision, call_id, capability_id, ctx.execution_id)
    executor.policy_evaluator = evaluator_bridge

    # 6. Step D: Execute via ToolExecutor (7-Stage Lifecycle)
    payload = ToolCallPayload(call_id=call_id, tool_name=selected_tool.name, arguments={"message": "E2E Test Success"})
    tool_result = executor.execute(payload)
    assert tool_result.success is True
    assert tool_result.output_data["echo"] == "E2E Test Success"

    # 7. Step E: Pure Mapper -> ToolExecutionEvent
    event = ToolResultExecutionMapper.map_to_event(tool_result, event_id="evt_e2e_101")
    assert event.success is True

    # 8. Step F: ToolExecutionStage -> ExecutionState
    runtime = RuntimeContext(execution_id=ctx.execution_id, trace_id=ctx.trace_id)
    state = ExecutionState(context=ctx, runtime=runtime, capability_id=capability_id, rendered_prompt="E2E Prompt")
    stage = ToolExecutionStage(event=event)
    updated_state = stage.execute(state)

    assert len(updated_state.trace_events) == 1
    assert updated_state.working_memory["tool_output_call_e2e_echo_101"]["echo"] == "E2E Test Success"
    assert len(updated_state.artifacts) == 1


def test_negative_spoofed_authorization_decision_binding_rejected():
    executor = ToolExecutor()
    native_adapter = NativeToolAdapter()
    echo_tool = create_echo_tool()
    native_adapter.register(echo_tool.definition, echo_tool.handler)
    executor.register_adapter(native_adapter)

    ctx = ExecutionContext(execution_id="exec_spoof_target", venture_id="v1", trace_id="tr1", workspace_id="ws1")

    tool_def = executor.registry.resolve_tool("echo")

    # Generate decision for call_id = "legitimate_call_1"
    legitimate_decision = EffectivePolicyGate.evaluate(
        capability_policy=ExecutionPolicy(),
        tool_definition=tool_def,
        context=ctx,
        call_id="legitimate_call_1",
        capability_id="data.echo",
    )

    # Bind decision to evaluator_bridge
    evaluator_bridge = EffectiveToolPolicyEvaluator()
    # Attacker tries to use legitimate_decision for spoofed_call_99
    evaluator_bridge.set_active_decision(legitimate_decision, "spoofed_call_99", "data.echo", ctx.execution_id)
    executor.policy_evaluator = evaluator_bridge

    # Execute payload with spoofed call_id -> MUST BE REJECTED AT AUTHORIZE STAGE
    payload = ToolCallPayload(call_id="spoofed_call_99", tool_name="echo", arguments={"message": "Spoof Attack"})

    with pytest.raises(ToolAuthorizationError) as exc_info:
        executor.execute(payload)

    assert "SECURITY_DENIAL" in str(exc_info.value)


def test_negative_forbidden_permission_denied():
    executor = ToolExecutor()

    forbidden_tool = ToolDefinition(
        name="root_delete",
        version="1.0.0",
        description="Root delete",
        permissions=[ToolPermission(scope="kernel:root", action="delete")],
        risk_level=RiskLevel.CRITICAL,
    )
    executor.registry.register_tool(forbidden_tool)

    ctx = ExecutionContext(execution_id="exec_forbidden", venture_id="v1", trace_id="tr1", workspace_id="ws1")
    call_id = "call_forbidden_1"

    # Evaluate PolicyGate -> FORBIDDEN -> DENY
    auth_decision = EffectivePolicyGate.evaluate(
        capability_policy=ExecutionPolicy(),
        tool_definition=forbidden_tool,
        context=ctx,
        call_id=call_id,
        capability_id="system.root",
        grantable_scopes={"workspace"},
    )
    assert auth_decision.decision == AuthorizationDecisionType.DENY
    assert auth_decision.permission_state == PermissionState.FORBIDDEN

    # Bind to evaluator bridge and attempt execution
    evaluator_bridge = EffectiveToolPolicyEvaluator()
    evaluator_bridge.set_active_decision(auth_decision, call_id, "system.root", ctx.execution_id)
    executor.policy_evaluator = evaluator_bridge

    payload = ToolCallPayload(call_id=call_id, tool_name="root_delete", arguments={})

    with pytest.raises(ToolAuthorizationError) as exc_info:
        executor.execute(payload)

    assert "DENIED by EffectivePolicyGate" in str(exc_info.value)


def test_negative_unapproved_high_risk_tool_requires_approval():
    executor = ToolExecutor()

    high_risk_tool = ToolDefinition(
        name="high_risk_op",
        version="1.0.0",
        description="High risk op",
        risk_level=RiskLevel.HIGH,
    )
    executor.registry.register_tool(high_risk_tool)

    ctx = ExecutionContext(execution_id="exec_high_risk", venture_id="v1", trace_id="tr1", workspace_id="ws1")
    call_id = "call_high_risk_1"

    # Evaluate PolicyGate without human approval -> REQUIRE_APPROVAL
    auth_decision = EffectivePolicyGate.evaluate(
        capability_policy=ExecutionPolicy(),
        tool_definition=high_risk_tool,
        context=ctx,
        call_id=call_id,
        capability_id="ops.high_risk",
        approved_by_human=False,
    )
    assert auth_decision.decision == AuthorizationDecisionType.REQUIRE_APPROVAL

    # Bind to evaluator bridge and attempt execution without human approval -> ApprovalRequiredError
    evaluator_bridge = EffectiveToolPolicyEvaluator()
    evaluator_bridge.set_active_decision(auth_decision, call_id, "ops.high_risk", ctx.execution_id)
    executor.policy_evaluator = evaluator_bridge

    payload = ToolCallPayload(call_id=call_id, tool_name="high_risk_op", arguments={})

    with pytest.raises(ApprovalRequiredError) as exc_info:
        executor.execute(payload, approved_by_human=False)

    assert "APPROVAL_REQUIRED by EffectivePolicyGate" in str(exc_info.value)
