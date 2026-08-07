"""
ExecutionStep & Tool Calling Schemas — ORION-114 Specification.
Provides ExecutionStep interface, ToolDefinition JSON schema, and ToolCall invocation models.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Protocol, runtime_checkable


@dataclass(frozen=True)
class ToolDefinition:
    """JSON Schema definition for an invokable tool / function calling primitive."""
    name: str
    description: str
    parameters_schema: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolCall:
    """Tool invocation payload produced by an AI model."""
    call_id: str
    function_name: str
    arguments: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ExecutionStep(Protocol):
    """Canonical interface for step execution in Agent Runtime workflows."""
    step_id: str
    step_type: str  # tool, llm, script, human_approval

    def execute_step(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...
