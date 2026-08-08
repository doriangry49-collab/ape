"""
Unit tests for ORION-117.0 Tool Abstraction Layer Contracts.
Verifies ToolDefinition immutability, ToolRegistry scoping, ToolPolicyEvaluator authorization & risk approval gates,
BaseToolAdapter protocol, 7-stage ToolExecutor lifecycle, and abstract EvidenceSink emission.
"""

from typing import List
import pytest

from ape.tools import (
    ApprovalRequiredError,
    BaseToolAdapter,
    DefaultEvidenceSink,
    PolicyDecision,
    RiskLevel,
    ToolAuthorizationError,
    ToolCallPayload,
    ToolDefinition,
    ToolExecutor,
    ToolLifecycleStage,
    ToolPermission,
    ToolRegistry,
    ToolResult,
    ToolScope,
)
from ape.tools.policy import ToolPolicyEvaluator


class DummyMockAdapter(BaseToolAdapter):
    """Mock ToolAdapter for testing protocol execution."""

    def __init__(self, tools: List[ToolDefinition]) -> None:
        self._tools = tools

    def list_tools(self) -> List[ToolDefinition]:
        return self._tools

    def execute_tool(self, payload: ToolCallPayload) -> ToolResult:
        return ToolResult(
            call_id=payload.call_id,
            tool_name=payload.tool_name,
            success=True,
            output_data={"result": f"Executed {payload.tool_name} with args {payload.arguments}"},
        )


def test_tool_definition_immutability():
    tool = ToolDefinition(
        name="read_file",
        version="1.0.0",
        description="Read file contents from local sandbox",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
        risk_level=RiskLevel.LOW,
    )

    assert tool.name == "read_file"
    assert tool.risk_level == RiskLevel.LOW
    with pytest.raises(AttributeError):
        tool.name = "write_file"  # Frozen dataclass check


def test_tool_registry_scoping():
    registry = ToolRegistry()

    t_global = ToolDefinition(name="global_tool", version="1.0.0", description="Global Tool")
    t_session = ToolDefinition(name="session_tool", version="2.0.0", description="Session Tool")

    registry.register_tool(t_global, scope=ToolScope.GLOBAL)
    registry.register_tool(t_session, scope=ToolScope.SESSION)

    assert registry.resolve_tool("global_tool").name == "global_tool"
    assert registry.resolve_tool("session_tool").version == "2.0.0"

    discovered = registry.discover_tools()
    names = [t.name for t in discovered]
    assert "global_tool" in names
    assert "session_tool" in names


def test_policy_evaluator_risk_and_approval():
    evaluator = ToolPolicyEvaluator()

    low_tool = ToolDefinition(name="low_tool", version="1.0", description="Low risk", risk_level=RiskLevel.LOW)
    high_tool = ToolDefinition(name="high_tool", version="1.0", description="High risk", risk_level=RiskLevel.HIGH)

    # Low risk -> Authorized
    res_low = evaluator.evaluate(low_tool)
    assert res_low.decision == PolicyDecision.AUTHORIZED

    # High risk without human approval -> Approval Required
    res_high = evaluator.evaluate(high_tool, approved_by_human=False)
    assert res_high.decision == PolicyDecision.APPROVAL_REQUIRED

    # High risk with human approval -> Authorized
    res_high_approved = evaluator.evaluate(high_tool, approved_by_human=True)
    assert res_high_approved.decision == PolicyDecision.AUTHORIZED


def test_executor_seven_stage_lifecycle():
    evidence_sink = DefaultEvidenceSink()
    executor = ToolExecutor(evidence_sink=evidence_sink)

    tool_def = ToolDefinition(
        name="calculate_hash",
        version="1.0.0",
        description="Calculates hash primitive",
        risk_level=RiskLevel.LOW,
    )
    adapter = DummyMockAdapter(tools=[tool_def])

    # DISCOVER & REGISTER stages
    executor.register_adapter(adapter)

    payload = ToolCallPayload(
        call_id="call_001",
        tool_name="calculate_hash",
        arguments={"data": "test_data"},
    )

    result = executor.execute(payload)

    assert result.success is True
    assert "Executed calculate_hash" in result.output_data["result"]
    assert result.evidence_hash != ""

    # Verify 7 Lifecycle Stages Emitted
    stages_emitted = [e["stage"] for e in evidence_sink.events]
    expected_stages = [
        ToolLifecycleStage.DISCOVER.value,
        ToolLifecycleStage.REGISTER.value,
        ToolLifecycleStage.AUTHORIZE.value,
        ToolLifecycleStage.RESOLVE.value,
        ToolLifecycleStage.EXECUTE.value,
        ToolLifecycleStage.RESULT.value,
        ToolLifecycleStage.EVIDENCE.value,
    ]
    for stage in expected_stages:
        assert stage in stages_emitted


def test_executor_blocks_unapproved_high_risk_tool():
    executor = ToolExecutor()

    high_tool = ToolDefinition(
        name="delete_database",
        version="1.0.0",
        description="Deletes database tables",
        risk_level=RiskLevel.CRITICAL,
    )
    adapter = DummyMockAdapter(tools=[high_tool])
    executor.register_adapter(adapter)

    payload = ToolCallPayload(call_id="c_002", tool_name="delete_database")

    with pytest.raises(ApprovalRequiredError):
        executor.execute(payload, approved_by_human=False)
