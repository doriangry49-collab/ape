"""
Unit tests for ORION-117.1 NativeToolAdapter & Reference Native Tools.
Verifies NativeToolAdapter dispatch, error normalization, reference tools (echo, structured_transform, deterministic_compute),
and 7-stage ToolExecutor lifecycle integration.
"""


from ape.tools import (
    DefaultEvidenceSink,
    NativeToolAdapter,
    ToolCallPayload,
    ToolExecutor,
    ToolLifecycleStage,
    ToolResult,
    create_deterministic_compute_tool,
    create_echo_tool,
    create_structured_transform_tool,
)


def test_native_tool_adapter_registration():
    adapter = NativeToolAdapter()
    echo_tool = create_echo_tool()

    adapter.register(echo_tool.definition, echo_tool.handler)

    tools = adapter.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "echo"
    assert tools[0].version == "1.0.0"


def test_native_echo_tool_execution():
    adapter = NativeToolAdapter()
    echo_tool = create_echo_tool()
    adapter.register(echo_tool.definition, echo_tool.handler)

    payload = ToolCallPayload(call_id="call_echo_1", tool_name="echo", arguments={"message": "Hello APE"})
    res = adapter.execute_tool(payload)

    assert isinstance(res, ToolResult)
    assert res.success is True
    assert res.output_data["echo"] == "Hello APE"


def test_native_structured_transform_tool():
    adapter = NativeToolAdapter()
    transform_tool = create_structured_transform_tool()
    adapter.register(transform_tool.definition, transform_tool.handler)

    # Filter operation
    payload_filter = ToolCallPayload(
        call_id="call_tf_1",
        tool_name="structured_transform",
        arguments={"operation": "filter", "data": {"a": 1, "b": 2, "c": 3}, "keys": ["a", "c"]},
    )
    res_filter = adapter.execute_tool(payload_filter)
    assert res_filter.success is True
    assert res_filter.output_data["transformed"] == {"a": 1, "c": 3}

    # Merge operation
    payload_merge = ToolCallPayload(
        call_id="call_tf_2",
        tool_name="structured_transform",
        arguments={"operation": "merge", "data": {"x": 10}, "secondary_data": {"y": 20}},
    )
    res_merge = adapter.execute_tool(payload_merge)
    assert res_merge.success is True
    assert res_merge.output_data["transformed"] == {"x": 10, "y": 20}


def test_native_deterministic_compute_tool():
    adapter = NativeToolAdapter()
    compute_tool = create_deterministic_compute_tool()
    adapter.register(compute_tool.definition, compute_tool.handler)

    # SHA256 Hash
    payload_hash = ToolCallPayload(
        call_id="c_h_1",
        tool_name="deterministic_compute",
        arguments={"operation": "hash", "input": "APE_ENGINE", "algorithm": "sha256"},
    )
    res_hash = adapter.execute_tool(payload_hash)
    assert res_hash.success is True
    assert len(res_hash.output_data["hash"]) == 64  # SHA-256 hex digest length

    # Sum Computation
    payload_sum = ToolCallPayload(
        call_id="c_s_1",
        tool_name="deterministic_compute",
        arguments={"operation": "sum", "numbers": [10, 20, 30.5]},
    )
    res_sum = adapter.execute_tool(payload_sum)
    assert res_sum.success is True
    assert res_sum.output_data["result"] == 60.5


def test_native_tool_exception_normalization():
    adapter = NativeToolAdapter()
    compute_tool = create_deterministic_compute_tool()
    adapter.register(compute_tool.definition, compute_tool.handler)

    # Unsupported operation raises ValueError inside handler
    payload_invalid = ToolCallPayload(
        call_id="c_err_1",
        tool_name="deterministic_compute",
        arguments={"operation": "invalid_op"},
    )
    res = adapter.execute_tool(payload_invalid)

    assert res.success is False
    assert "Unsupported compute operation" in res.error_message


def test_executor_lifecycle_with_native_adapter():
    evidence_sink = DefaultEvidenceSink()
    executor = ToolExecutor(evidence_sink=evidence_sink)

    adapter = NativeToolAdapter()
    echo_tool = create_echo_tool()
    adapter.register(echo_tool.definition, echo_tool.handler)

    # Register NativeToolAdapter with ToolExecutor
    executor.register_adapter(adapter)

    payload = ToolCallPayload(call_id="exec_call_100", tool_name="echo", arguments={"message": "Lifecycle Integration"})
    res = executor.execute(payload)

    assert res.success is True
    assert res.output_data["echo"] == "Lifecycle Integration"
    assert res.evidence_hash != ""

    # Verify 7 Lifecycle Stages Emitted
    emitted_stages = [e["stage"] for e in evidence_sink.events]
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
        assert stage in emitted_stages
