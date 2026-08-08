"""
MCP Adapter Wire Messages & Dataclasses — ORION-117.2 Specification.
Defines JSON-RPC 2.0 message models, MCP session states, and transport configurations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class MCPSessionState(str, Enum):
    """MCP Client Session State Machine."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    INITIALIZING = "initializing"
    NEGOTIATING = "negotiating"
    READY = "ready"
    CLOSED = "closed"


@dataclass(frozen=True)
class JSONRPCRequest:
    """JSON-RPC 2.0 Request Payload."""
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    method: str = ""
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class JSONRPCResponse:
    """JSON-RPC 2.0 Response Payload."""
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class TransportConfig:
    """Configuration options for MCP Transports."""
    transport_type: str  # "stdio" or "http_streamable"
    command: Optional[str] = None  # for stdio
    args: list = field(default_factory=list)  # for stdio
    url: Optional[str] = None  # for http_streamable
    timeout_ms: float = 30000.0
    headers: Dict[str, str] = field(default_factory=dict)
