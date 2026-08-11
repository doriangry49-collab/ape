"""
MCPToolAdapter Implementation — ORION-117.2 Specification.
Bridges APE Tool Layer calls to MCPClient, handling schema translation and result mapping.
"""

import time
from typing import Dict, List

from ape.tools.adapters.base import BaseToolAdapter
from ape.tools.adapters.mcp.client import MCPClient
from ape.tools.adapters.mcp.mapper import MCPToolMapper
from ape.tools.contracts import ToolCallPayload, ToolResult
from ape.tools.definition import ToolDefinition


class MCPToolAdapter(BaseToolAdapter):
    """Adapter bridging APE Tool Layer to an external MCP Server via MCPClient."""

    def __init__(self, client: MCPClient) -> None:
        self.client = client
        self._tool_map: Dict[str, ToolDefinition] = {}
        self._invalidated = True

    def invalidate_discovery_cache(self) -> None:
        """Mark discovery cache as invalidated when notifications/tools/list_changed arrives."""
        self._invalidated = True

    def list_tools(self) -> List[ToolDefinition]:
        """Fetch MCP tools list via client and return mapped APE ToolDefinitions."""
        if not self._invalidated and self._tool_map:
            return list(self._tool_map.values())

        if self.client.state.value in ("disconnected", "closed"):
            self.client.connect_and_initialize()

        mcp_res = self.client.list_tools()
        mcp_tools = mcp_res.get("tools", [])

        self._tool_map.clear()
        for mcp_tool in mcp_tools:
            tool_def = MCPToolMapper.mcp_tool_to_definition(mcp_tool, server_id=self.client.server_id)
            self._tool_map[tool_def.name] = tool_def

        self._invalidated = False
        return list(self._tool_map.values())

    def execute_tool(self, payload: ToolCallPayload) -> ToolResult:
        """Execute tool payload against remote MCP server via MCPClient."""
        start_time = time.time()

        if payload.tool_name not in self._tool_map:
            # Refresh list if tool not cached
            self.list_tools()

        if payload.tool_name not in self._tool_map:
            dur_ms = round((time.time() - start_time) * 1000.0, 2)
            return ToolResult(
                call_id=payload.call_id,
                tool_name=payload.tool_name,
                success=False,
                error_message=f"MCP Tool '{payload.tool_name}' not found on server '{self.client.server_id}'.",
                duration_ms=dur_ms,
            )

        tool_def = self._tool_map[payload.tool_name]
        remote_name = tool_def.metadata.get("remote_name", payload.tool_name)

        try:
            mcp_res = self.client.call_tool(remote_name, payload.arguments)
            dur_ms = round((time.time() - start_time) * 1000.0, 2)
            return MCPToolMapper.mcp_result_to_tool_result(
                call_id=payload.call_id,
                tool_name=payload.tool_name,
                mcp_result=mcp_res,
                duration_ms=dur_ms,
            )
        except Exception as err:
            dur_ms = round((time.time() - start_time) * 1000.0, 2)
            return ToolResult(
                call_id=payload.call_id,
                tool_name=payload.tool_name,
                success=False,
                error_message=f"MCP Tool execution failed: {str(err)}",
                duration_ms=dur_ms,
            )
