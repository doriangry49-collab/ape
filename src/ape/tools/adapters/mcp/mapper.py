"""
MCP Schema & Result Mapper — ORION-117.2 Specification.
Converts MCP Tool schemas to APE ToolDefinition and MCP call results to APE ToolResult.
Enforces schema compatibility checks and structural output validation without semantic sanitization.
"""

import json
from typing import Any, Dict

from ape.tools.contracts import ToolResult
from ape.tools.definition import RiskLevel, ToolDefinition, ToolPermission


class MCPToolMapper:
    """Utility class mapping MCP protocol objects to APE Tool Layer primitives."""

    @staticmethod
    def _check_schema_depth(schema: Any, current_depth: int = 0, max_depth: int = 10) -> int:
        if current_depth > max_depth:
            raise ValueError(f"MCP Schema depth exceeds maximum limit of {max_depth}.")
        if isinstance(schema, dict):
            return max([current_depth] + [MCPToolMapper._check_schema_depth(v, current_depth + 1, max_depth) for v in schema.values()])
        elif isinstance(schema, list):
            return max([current_depth] + [MCPToolMapper._check_schema_depth(item, current_depth + 1, max_depth) for item in schema])
        return current_depth

    @staticmethod
    def mcp_tool_to_definition(mcp_tool: Dict[str, Any], server_id: str = "default_server") -> ToolDefinition:
        """
        Converts MCP Tool schema to APE ToolDefinition.
        Enforces APE Schema Security Compatibility checks (max depth 10, max properties 100, max size 64KB).
        Stores remote_name, server_id, and namespace inside ToolDefinition.metadata.
        """
        name = mcp_tool.get("name", "")
        if not name:
            raise ValueError("MCP Tool definition missing 'name'.")

        description = mcp_tool.get("description", "")
        input_schema = mcp_tool.get("inputSchema", {})

        # Schema Security Checks
        schema_bytes = len(json.dumps(input_schema).encode("utf-8"))
        if schema_bytes > 65536:
            raise ValueError(f"MCP Tool schema size ({schema_bytes} bytes) exceeds maximum limit of 64KB.")

        props = input_schema.get("properties", {})
        if len(props) > 100:
            raise ValueError(f"MCP Tool property count ({len(props)}) exceeds maximum limit of 100.")

        MCPToolMapper._check_schema_depth(input_schema, max_depth=10)

        # Build metadata dictionary preserving remote_name and server_id
        metadata = {
            "remote_name": name,
            "server_id": server_id,
            "namespace": f"mcp:{server_id}",
            "mcp_original_name": name,
        }

        # APE canonical name
        canonical_name = f"mcp_{server_id}_{name}"

        return ToolDefinition(
            name=canonical_name,
            version="1.0.0",
            description=description,
            input_schema=input_schema,
            permissions=[ToolPermission(scope=f"mcp:{server_id}", action="execute")],
            risk_level=RiskLevel.MEDIUM,
            metadata=metadata,
        )

    @staticmethod
    def mcp_result_to_tool_result(call_id: str, tool_name: str, mcp_result: Dict[str, Any], duration_ms: float = 0.0) -> ToolResult:
        """
        Converts MCP call result dictionary to APE ToolResult.
        Performs structural output validation (payload size cap 10MB, type normalization).
        Does NOT perform semantic text filtering (preserves raw content integrity).
        """
        is_error = bool(mcp_result.get("isError", False))
        content_items = mcp_result.get("content", [])

        # Structural Output Validation: Size cap 10MB
        raw_bytes = len(json.dumps(mcp_result).encode("utf-8"))
        if raw_bytes > 10485760:
            return ToolResult(
                call_id=call_id,
                tool_name=tool_name,
                success=False,
                error_message=f"MCP result payload size ({raw_bytes} bytes) exceeds maximum structural limit of 10MB.",
                duration_ms=duration_ms,
            )

        extracted_text = []
        structured_content = []

        if isinstance(content_items, list):
            for item in content_items:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        extracted_text.append(item.get("text", ""))
                    structured_content.append(item)

        output_data = {
            "text": "\n".join(extracted_text),
            "content": structured_content,
            "raw_mcp_result": mcp_result,
        }

        if is_error:
            error_msg = output_data["text"] or "MCP Tool reported execution error."
            return ToolResult(
                call_id=call_id,
                tool_name=tool_name,
                success=False,
                output_data=output_data,
                error_message=error_msg,
                duration_ms=duration_ms,
            )

        return ToolResult(
            call_id=call_id,
            tool_name=tool_name,
            success=True,
            output_data=output_data,
            duration_ms=duration_ms,
        )
