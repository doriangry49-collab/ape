"""
MCP Client & Session Lifecycle Manager — ORION-117.2 Specification.
Manages JSON-RPC 2.0 wire protocol requests and the MCP Session Lifecycle.
"""

from typing import Any, Dict, Optional

from ape.tools.adapters.mcp.contracts import JSONRPCRequest, MCPSessionState
from ape.tools.adapters.mcp.transports import MCPTransport


class MCPClient:
    """Manages MCP Session Lifecycle and JSON-RPC 2.0 requests over an MCPTransport."""

    def __init__(self, transport: MCPTransport, server_id: str = "default_mcp_server") -> None:
        self.transport = transport
        self.server_id = server_id
        self.state = MCPSessionState.DISCONNECTED
        self._request_counter = 0

    def _next_id(self) -> int:
        self._request_counter += 1
        return self._request_counter

    def connect_and_initialize(
        self,
        client_info: Optional[Dict[str, Any]] = None,
        capabilities: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Connect transport and perform MCP session initialization and capability negotiation."""
        self.state = MCPSessionState.CONNECTING
        self.transport.connect()

        self.state = MCPSessionState.INITIALIZING
        req_id = self._next_id()
        init_request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": client_info or {"name": "APE_Engine", "version": "1.0.0"},
                "capabilities": capabilities or {"tools": {"listChanged": True}},
            },
        }

        self.transport.send_message(init_request)
        response = self.transport.receive_message()

        self.state = MCPSessionState.NEGOTIATING
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
        self.transport.send_message(initialized_notification)

        self.state = MCPSessionState.READY
        return response.get("result", {})

    def list_tools(self, cursor: Optional[str] = None) -> Dict[str, Any]:
        """Send tools/list RPC request."""
        if self.state != MCPSessionState.READY:
            raise RuntimeError(f"MCPClient is not in READY state (current: {self.state.value}).")

        req_id = self._next_id()
        params = {}
        if cursor:
            params["cursor"] = cursor

        req = {"jsonrpc": "2.0", "id": req_id, "method": "tools/list", "params": params}
        self.transport.send_message(req)
        response = self.transport.receive_message()

        if "error" in response and response["error"]:
            err = response["error"]
            raise RuntimeError(f"MCP tools/list failed: {err.get('message', 'Unknown error')}")

        return response.get("result", {})

    def call_tool(self, tool_name: str, arguments: Dict[str, Any], timeout_ms: float = 30000.0) -> Dict[str, Any]:
        """Send tools/call RPC request."""
        if self.state != MCPSessionState.READY:
            raise RuntimeError(f"MCPClient is not in READY state (current: {self.state.value}).")

        req_id = self._next_id()
        req = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        self.transport.send_message(req)
        response = self.transport.receive_message(timeout_ms=timeout_ms)

        if "error" in response and response["error"]:
            err = response["error"]
            raise RuntimeError(f"MCP tools/call failed: {err.get('message', 'Unknown error')}")

        return response.get("result", {})

    def close(self) -> None:
        """Close session and transport."""
        if self.transport.is_connected:
            self.transport.close()
        self.state = MCPSessionState.CLOSED
