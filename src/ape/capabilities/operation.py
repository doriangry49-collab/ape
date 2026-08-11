"""
ExecutionOperation & Compensation Pattern — ORION-115 Specification.
Defines ExecutionOperation Protocol supporting execute, rollback, and compensate.
"""

from typing import Any, Protocol, runtime_checkable

from ape.capabilities.contracts import ExecutionState


@runtime_checkable
class ExecutionOperation(Protocol):
    """Canonical ExecutionOperation Protocol supporting rollback and compensation transactions."""
    operation_id: str
    operation_type: str

    def execute(self, state: ExecutionState) -> ExecutionState:
        ...

    def rollback(self, state: ExecutionState) -> ExecutionState:
        ...

    def compensate(self, state: ExecutionState) -> ExecutionState:
        ...


class BaseOperation:
    """Base operation implementation with default no-op rollback and compensate."""
    operation_id: str = "op_base"
    operation_type: str = "base"

    def execute(self, state: ExecutionState) -> ExecutionState:
        return state

    def rollback(self, state: ExecutionState) -> ExecutionState:
        return state

    def compensate(self, state: ExecutionState) -> ExecutionState:
        return state


class ProviderOperation(BaseOperation):
    """Operation performing LLM provider invocation."""
    operation_id: str = "op_provider"
    operation_type: str = "provider"

    def __init__(self, provider_adapter: Any) -> None:
        self.provider_adapter = provider_adapter

    def execute(self, state: ExecutionState) -> ExecutionState:
        res = self.provider_adapter.execute(state.rendered_prompt, state.capability_id, state.context)
        state.result = res
        return state


class ToolOperation(BaseOperation):
    """Operation executing an external tool call."""
    operation_id: str = "op_tool"
    operation_type: str = "tool"

    def __init__(self, tool_call: Any) -> None:
        self.tool_call = tool_call

    def execute(self, state: ExecutionState) -> ExecutionState:
        state.working_memory[f"tool_{self.tool_call.function_name}"] = "Executed"
        return state

    def compensate(self, state: ExecutionState) -> ExecutionState:
        state.working_memory[f"tool_{self.tool_call.function_name}"] = "Compensated"
        return state


class FileOperation(BaseOperation):
    """Operation writing artifacts to disk."""
    operation_id: str = "op_file"
    operation_type: str = "file"

    def __init__(self, artifact: Any) -> None:
        self.artifact = artifact

    def execute(self, state: ExecutionState) -> ExecutionState:
        state.artifacts.append(self.artifact)
        return state

    def rollback(self, state: ExecutionState) -> ExecutionState:
        state.artifacts = [a for a in state.artifacts if a.artifact_id != self.artifact.artifact_id]
        return state
