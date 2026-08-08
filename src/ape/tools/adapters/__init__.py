"""
APE Tool Adapters Package — ORION-117.1 Specification.
Exports BaseToolAdapter protocol interface and NativeToolAdapter implementation.
"""

from ape.tools.adapters.base import BaseToolAdapter
from ape.tools.adapters.mcp import MCPClient, MCPToolAdapter, MCPToolMapper, StdioTransport
from ape.tools.adapters.native import (
    NativeTool,
    NativeToolAdapter,
    create_deterministic_compute_tool,
    create_echo_tool,
    create_structured_transform_tool,
)

__all__ = [
    "BaseToolAdapter",
    "NativeTool",
    "NativeToolAdapter",
    "create_echo_tool",
    "create_structured_transform_tool",
    "create_deterministic_compute_tool",
    "MCPToolAdapter",
    "MCPClient",
    "MCPToolMapper",
    "StdioTransport",
]
