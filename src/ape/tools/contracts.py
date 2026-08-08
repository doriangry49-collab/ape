"""
Tool Lifecycle & Exception Hierarchy Contracts — ORION-117.0 Specification.
Defines the 7-stage Tool Lifecycle, Exception Hierarchy, ToolCallPayload, ToolResult, and abstract EvidenceSink protocol.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Protocol, runtime_checkable

from ape.tools.definition import ToolDefinition


class ToolLifecycleStage(str, Enum):
    """Canonical 7-stage lifecycle for Tool execution."""
    DISCOVER = "discover"
    REGISTER = "register"
    AUTHORIZE = "authorize"
    RESOLVE = "resolve"
    EXECUTE = "execute"
    RESULT = "result"
    EVIDENCE = "evidence"


class ToolError(Exception):
    """Base exception for all tool abstraction errors."""
    pass


class ToolNotFoundError(ToolError):
    """Raised when requested tool name/version is not registered."""
    pass


class ToolAuthorizationError(ToolError):
    """Raised when policy evaluation denies tool execution."""
    pass


class ApprovalRequiredError(ToolAuthorizationError):
    """Raised when tool execution requires explicit human/releaser approval."""
    pass


class ToolExecutionError(ToolError):
    """Raised when tool execution fails in the adapter layer."""
    pass


@dataclass(frozen=True)
class ToolCallPayload:
    """Immutable payload representing an invocation request for a tool."""
    call_id: str
    tool_name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    tool_version: Optional[str] = None
    execution_context_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolResult:
    """Standardized normalized execution response produced by tool execution."""
    call_id: str
    tool_name: str
    success: bool
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    duration_ms: float = 0.0
    evidence_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class EvidenceSink(Protocol):
    """Abstract interface for governance evidence logging (decoupled from storage implementations)."""

    def emit_evidence(self, stage: ToolLifecycleStage, event_data: Dict[str, Any]) -> str:
        """Emit an evidence event and return a SHA-256 evidence hash."""
        ...
