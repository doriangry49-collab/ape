"""
BaseToolAdapter Protocol Interface — ORION-117.0 Specification.
Defines minimal provider-agnostic interface for tool adapters.
"""

from abc import ABC, abstractmethod
from typing import List

from ape.tools.contracts import ToolCallPayload, ToolResult
from ape.tools.definition import ToolDefinition


class BaseToolAdapter(ABC):
    """Abstract base class for all tool adapters (Native, MCP, HTTP, Browser, etc.)."""

    @abstractmethod
    def list_tools(self) -> List[ToolDefinition]:
        """Return list of ToolDefinitions exposed by this adapter."""
        ...

    @abstractmethod
    def execute_tool(self, payload: ToolCallPayload) -> ToolResult:
        """Execute a tool call payload and return normalized ToolResult."""
        ...
