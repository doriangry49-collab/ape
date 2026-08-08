"""
NativeToolAdapter Implementation — ORION-117.1 Specification.
Provides reference implementation of BaseToolAdapter for Python callables.
Includes safe, deterministic reference tools (echo, structured_transform, deterministic_compute).
"""

from dataclasses import dataclass
import hashlib
from typing import Any, Callable, Dict, List, Optional

from ape.tools.adapters.base import BaseToolAdapter
from ape.tools.contracts import ToolCallPayload, ToolExecutionError, ToolResult
from ape.tools.definition import RiskLevel, ToolDefinition, ToolPermission


@dataclass
class NativeTool:
    """Wrapper pairing a ToolDefinition with a Python callable handler."""
    definition: ToolDefinition
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]


class NativeToolAdapter(BaseToolAdapter):
    """Adapter for executing Python native callable functions without external side-effects."""

    def __init__(self) -> None:
        self._tools: Dict[str, NativeTool] = {}

    def register(self, definition: ToolDefinition, handler: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        """Register a NativeTool definition and callable handler."""
        self._tools[definition.name] = NativeTool(definition=definition, handler=handler)

    def list_tools(self) -> List[ToolDefinition]:
        """Return list of ToolDefinitions for all registered native tools."""
        return [tool.definition for tool in self._tools.values()]

    def execute_tool(self, payload: ToolCallPayload) -> ToolResult:
        """Execute a native tool payload and normalize Python exceptions into ToolResult."""
        if payload.tool_name not in self._tools:
            return ToolResult(
                call_id=payload.call_id,
                tool_name=payload.tool_name,
                success=False,
                error_message=f"Native tool '{payload.tool_name}' is not registered in this adapter.",
            )

        native_tool = self._tools[payload.tool_name]
        try:
            output = native_tool.handler(payload.arguments)
            return ToolResult(
                call_id=payload.call_id,
                tool_name=payload.tool_name,
                success=True,
                output_data=output,
            )
        except Exception as err:
            return ToolResult(
                call_id=payload.call_id,
                tool_name=payload.tool_name,
                success=False,
                error_message=f"Native tool execution failed: {str(err)}",
            )


# --- Reference Native Tools (Zero Side-Effects) ---

def create_echo_tool() -> NativeTool:
    """Creates reference 'echo' tool echoing input message."""
    def handler(args: Dict[str, Any]) -> Dict[str, Any]:
        msg = args.get("message", "")
        return {"echo": str(msg), "received_keys": list(args.keys())}

    defn = ToolDefinition(
        name="echo",
        version="1.0.0",
        description="Echoes input payload for testing and verification",
        input_schema={"type": "object", "properties": {"message": {"type": "string"}}},
        risk_level=RiskLevel.LOW,
    )
    return NativeTool(definition=defn, handler=handler)


def create_structured_transform_tool() -> NativeTool:
    """Creates reference 'structured_transform' tool for JSON/dict key filtering or dictionary merging."""
    def handler(args: Dict[str, Any]) -> Dict[str, Any]:
        op = args.get("operation", "filter")
        data = args.get("data", {})
        if not isinstance(data, dict):
            raise ValueError("Argument 'data' must be a dictionary.")

        if op == "filter":
            allowed_keys = set(args.get("keys", []))
            filtered = {k: v for k, v in data.items() if k in allowed_keys}
            return {"transformed": filtered}
        elif op == "merge":
            secondary = args.get("secondary_data", {})
            if not isinstance(secondary, dict):
                raise ValueError("Argument 'secondary_data' must be a dictionary.")
            merged = {**data, **secondary}
            return {"transformed": merged}
        else:
            raise ValueError(f"Unsupported transform operation '{op}'. Supported: filter, merge.")

    defn = ToolDefinition(
        name="structured_transform",
        version="1.0.0",
        description="Transforms dictionaries via deterministic key filtering or merging",
        input_schema={
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["filter", "merge"]},
                "data": {"type": "object"},
                "keys": {"type": "array", "items": {"type": "string"}},
            },
        },
        risk_level=RiskLevel.LOW,
    )
    return NativeTool(definition=defn, handler=handler)


def create_deterministic_compute_tool() -> NativeTool:
    """Creates reference 'deterministic_compute' tool for mathematical and cryptographic hashing (NO eval/exec)."""
    def handler(args: Dict[str, Any]) -> Dict[str, Any]:
        op = args.get("operation", "hash")

        if op == "hash":
            text = str(args.get("input", ""))
            algo = str(args.get("algorithm", "sha256")).lower()
            if algo == "sha256":
                digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            elif algo == "md5":
                digest = hashlib.md5(text.encode("utf-8")).hexdigest()
            else:
                raise ValueError(f"Unsupported hash algorithm '{algo}'. Supported: sha256, md5.")
            return {"algorithm": algo, "hash": digest}

        elif op == "sum":
            numbers = args.get("numbers", [])
            if not isinstance(numbers, list) or not all(isinstance(n, (int, float)) for n in numbers):
                raise ValueError("Argument 'numbers' must be a list of numeric values.")
            return {"operation": "sum", "result": sum(numbers)}

        elif op == "multiply":
            numbers = args.get("numbers", [])
            if not isinstance(numbers, list) or not all(isinstance(n, (int, float)) for n in numbers):
                raise ValueError("Argument 'numbers' must be a list of numeric values.")
            total = 1.0
            for num in numbers:
                total *= num
            return {"operation": "multiply", "result": total}

        else:
            raise ValueError(f"Unsupported compute operation '{op}'. Supported: hash, sum, multiply.")

    defn = ToolDefinition(
        name="deterministic_compute",
        version="1.0.0",
        description="Performs predefined mathematical and hashing computations deterministically without side-effects",
        input_schema={
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["hash", "sum", "multiply"]},
                "input": {"type": "string"},
                "numbers": {"type": "array", "items": {"type": "number"}},
            },
        },
        risk_level=RiskLevel.LOW,
    )
    return NativeTool(definition=defn, handler=handler)
