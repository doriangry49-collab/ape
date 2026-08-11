"""
Unit tests for ORION-117.2 MCPToolAdapter & Mock MCP Transport.
Verifies MCPToolMapper schema security checks, structural output validation, MCPClient session lifecycle,
MCPToolAdapter RPC dispatching, and 7-stage ToolExecutor integration.
"""

from typing import Any, Dict, List

import pytest

from ape.tools import (
    DefaultEvidenceSink,
    MCPClient,
    MCPToolAdapter,
    MCPToolMapper,
    ToolCallPayload,
    ToolExecutor,
    ToolLifecycleStage,
    ToolResult,
)
from ape.tools.adapters.mcp.transports import MCPTransport


class MockMCPTransport(MCPTransport):
    """Mock MCPTransport simulating an MCP Server over JSON-RPC 2.0 for unit testing."""

    def __init__(self) -> None:
        self._connected = False
        self.sent_messages: List[Dict[str, Any]] = []
        self.mock_tools = [
            {
                "name": "search_db",
                "description": "Searches remote database",
                "inputSchema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                },
            }
        ]

    def connect(self) -> None:
        self._connected = True

    def send_message(self, message: Dict[str, Any]) -> None:
        self.sent_messages.append(message)

    def receive_message(self, timeout_ms: float = 30000.0) -> Dict[str, Any]:
        if not self.sent_messages:
            raise RuntimeError("No message to reply to.")

        last_msg = self.sent_messages[-1]
        method = last_msg.get("method")
        msg_id = last_msg.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "Mock_MCP_Server", "version": "1.0.0"},
                    "capabilities": {"tools": {}},
                },
            }
        elif method == "notifications/initialized":
            return {}
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": self.mock_tools},
            }
        elif method == "tools/call":
            params = last_msg.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            if name == "search_db":
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Results for '{args.get('query')}'"}],
                        "isError": False,
                    },
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Unknown tool '{name}'"}],
                        "isError": True,
                    },
                }
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

    def close(self) -> None:
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected


def test_mcp_tool_mapper_schema_security():
    mcp_tool = {
        "name": "create_issue",
        "description": "Creates a GitHub issue",
        "inputSchema": {
            "type": "object",
            "properties": {"title": {"type": "string"}, "body": {"type": "string"}},
        },
    }

    tool_def = MCPToolMapper.mcp_tool_to_definition(mcp_tool, server_id="github")

    assert tool_def.name == "mcp_github_create_issue"
    assert tool_def.metadata["remote_name"] == "create_issue"
    assert tool_def.metadata["server_id"] == "github"
    assert tool_def.metadata["namespace"] == "mcp:github"


def test_mcp_tool_mapper_schema_depth_limit():
    # Build recursive nested schema exceeding depth 10
    nested: Dict[str, Any] = {"type": "string"}
    for _ in range(12):
        nested = {"type": "object", "properties": {"nested": nested}}

    deep_mcp_tool = {"name": "deep_tool", "description": "Deep nesting", "inputSchema": nested}

    with pytest.raises(ValueError, match="depth exceeds maximum limit"):
        MCPToolMapper.mcp_tool_to_definition(deep_mcp_tool, server_id="malicious")


def test_mcp_client_session_lifecycle():
    transport = MockMCPTransport()
    client = MCPClient(transport=transport, server_id="mock_srv")

    res = client.connect_and_initialize()
    assert client.state.value == "ready"
    assert res.get("serverInfo", {}).get("name") == "Mock_MCP_Server"

    tools_res = client.list_tools()
    assert len(tools_res.get("tools", [])) == 1

    client.close()
    assert client.state.value == "closed"


def test_mcp_tool_adapter_list_and_execute():
    transport = MockMCPTransport()
    client = MCPClient(transport=transport, server_id="test_srv")
    adapter = MCPToolAdapter(client=client)

    tools = adapter.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "mcp_test_srv_search_db"

    payload = ToolCallPayload(
        call_id="call_mcp_1",
        tool_name="mcp_test_srv_search_db",
        arguments={"query": "constitutional pipeline"},
    )

    result = adapter.execute_tool(payload)

    assert isinstance(result, ToolResult)
    assert result.success is True
    assert "Results for 'constitutional pipeline'" in result.output_data["text"]


def test_executor_seven_stage_lifecycle_with_mcp_adapter():
    evidence_sink = DefaultEvidenceSink()
    executor = ToolExecutor(evidence_sink=evidence_sink)

    transport = MockMCPTransport()
    client = MCPClient(transport=transport, server_id="remote_mcp")
    adapter = MCPToolAdapter(client=client)

    executor.register_adapter(adapter)

    payload = ToolCallPayload(
        call_id="mcp_exec_99",
        tool_name="mcp_remote_mcp_search_db",
        arguments={"query": "ORION-117.2 Spec"},
    )

    result = executor.execute(payload)

    assert result.success is True
    assert "Results for 'ORION-117.2 Spec'" in result.output_data["text"]
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
