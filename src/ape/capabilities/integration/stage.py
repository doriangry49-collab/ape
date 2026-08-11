"""
ToolExecutionStage Runner — ORION-118 Specification.
Applies ToolExecutionEvent outputs to ExecutionState (working_memory, artifacts, trace_events)
without violating pure mapper invariants.
"""

from typing import Optional

from ape.capabilities.artifacts import ArtifactType, ExecutionArtifact
from ape.capabilities.contracts import ExecutionState
from ape.capabilities.integration.contracts import ToolExecutionEvent
from ape.capabilities.pipeline import BaseExecutionStage
from ape.capabilities.resiliency import RuntimeEvent


class ToolExecutionStage(BaseExecutionStage):
    """Pipeline stage integrating ToolExecutionEvent into ExecutionState."""
    stage_name: str = "ToolExecutionStage"

    def __init__(self, event: Optional[ToolExecutionEvent] = None) -> None:
        self.event = event

    def set_event(self, event: ToolExecutionEvent) -> None:
        """Bind target ToolExecutionEvent for stage execution."""
        self.event = event

    def execute(self, state: ExecutionState) -> ExecutionState:
        """Apply ToolExecutionEvent outputs, artifacts, and trace events to state."""
        if self.event is None:
            return state

        evt = self.event

        # 1. Append trace event
        state.trace_events.append(
            RuntimeEvent(
                event_type="ToolExecutionCompleted" if evt.success else "ToolExecutionFailed",
                capability_id=state.capability_id,
                trace_id=state.context.trace_id,
                details={
                    "call_id": evt.call_id,
                    "tool_name": evt.tool_name,
                    "success": evt.success,
                    "duration_ms": evt.duration_ms,
                    "evidence_hash": evt.evidence_hash,
                    "error_message": evt.error_message,
                },
            )
        )

        # 2. Update working memory
        if evt.success:
            state.working_memory[f"tool_output_{evt.call_id}"] = evt.output_data
            state.working_memory[f"tool_latest_{evt.tool_name}"] = evt.output_data
        else:
            state.working_memory[f"tool_error_{evt.call_id}"] = evt.error_message

        # 3. Append execution artifact if output present
        if evt.output_data:
            artifact = ExecutionArtifact(
                artifact_id=f"art_tool_{evt.call_id}",
                artifact_type=ArtifactType.TOOL_OUTPUT,
                name=f"tool_output_{evt.call_id}",
                content=evt.output_data,
                mime_type="application/json",
                metadata={"tool_name": evt.tool_name, "evidence_hash": evt.evidence_hash},
            )
            state.artifacts.append(artifact)

        return state
