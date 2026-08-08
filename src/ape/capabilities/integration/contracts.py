"""
Capability ↔ Tool ↔ Execution Integration Contracts — ORION-118 Specification.
Defines ToolCandidate, ResolutionResult, CapabilityToolResolver ABC, ToolExecutionEvent, and ToolResultExecutionMapper.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ape.capabilities.contracts import ExecutionContext
from ape.tools.contracts import ToolResult
from ape.tools.definition import ToolDefinition
from ape.tools.registry import ToolRegistry, ToolScope


@dataclass(frozen=True)
class ToolCandidate:
    """Immutable candidate tool bound to an adapter identity and scope."""
    tool_definition: ToolDefinition
    adapter_id: str
    locality: str  # "native" or "mcp"
    registry_scope: ToolScope = ToolScope.GLOBAL
    estimated_cost: float = 0.0


@dataclass(frozen=True)
class ResolutionResult:
    """Outcome of resolving a Capability request to a concrete ToolCandidate."""
    capability_id: str
    selected_candidate: ToolCandidate
    resolution_strategy: str
    candidate_count: int


class CapabilityToolResolver(ABC):
    """Abstract resolver mapping high-level Capability ID to concrete ToolCandidates."""

    @abstractmethod
    def resolve_tool_for_capability(
        self,
        capability_id: str,
        registry: ToolRegistry,
        context: ExecutionContext,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> ResolutionResult:
        """Resolve Capability ID to a ToolCandidate without executing the tool."""
        ...


@dataclass(frozen=True)
class ToolExecutionEvent:
    """Canonical execution event produced from a tool result."""
    event_id: str
    call_id: str
    tool_name: str
    success: bool
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    evidence_hash: str = ""
    duration_ms: float = 0.0


class ToolResultExecutionMapper:
    """Pure transformer converting raw ToolResult to ToolExecutionEvent without mutating ExecutionState."""

    @staticmethod
    def map_to_event(tool_result: ToolResult, event_id: Optional[str] = None) -> ToolExecutionEvent:
        """Pure transformation: ToolResult -> ToolExecutionEvent (No State Mutation)."""
        evt_id = event_id or f"evt_tool_{tool_result.call_id}"
        return ToolExecutionEvent(
            event_id=evt_id,
            call_id=tool_result.call_id,
            tool_name=tool_result.tool_name,
            success=tool_result.success,
            output_data=tool_result.output_data,
            error_message=tool_result.error_message,
            evidence_hash=tool_result.evidence_hash,
            duration_ms=tool_result.duration_ms,
        )
