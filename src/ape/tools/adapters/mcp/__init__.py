"""
MCP Tool Adapter Subsystem — ORION-117.2 Specification.
Exports MCPToolAdapter, MCPClient, MCPTransport, StdioTransport, HTTPStreamableTransport, and MCPToolMapper.
"""

from ape.tools.adapters.mcp.adapter import MCPToolAdapter
from ape.tools.adapters.mcp.client import MCPClient
from ape.tools.adapters.mcp.contracts import JSONRPCRequest, JSONRPCResponse, MCPSessionState, TransportConfig
from ape.tools.adapters.mcp.mapper import MCPToolMapper
from ape.tools.adapters.mcp.transports import HTTPStreamableTransport, MCPTransport, StdioTransport

__all__ = [
    "MCPToolAdapter",
    "MCPClient",
    "MCPSessionState",
    "JSONRPCRequest",
    "JSONRPCResponse",
    "TransportConfig",
    "MCPTransport",
    "StdioTransport",
    "HTTPStreamableTransport",
    "MCPToolMapper",
]
