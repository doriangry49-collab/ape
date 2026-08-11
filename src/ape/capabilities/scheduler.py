"""
ExecutionScheduler Specification — ORION-115 Specification.
Defines ExecutionScheduler Protocol, SequentialScheduler, and ParallelScheduler decoupled from ExecutionGraph topology.
"""

from typing import Any, Protocol, runtime_checkable

from ape.capabilities.contracts import ExecutionResult, ExecutionState
from ape.capabilities.graph import ExecutionGraph
from ape.capabilities.request import ExecutionRequest
from ape.capabilities.trace import ExecutionTraceBuilder


@runtime_checkable
class ExecutionScheduler(Protocol):
    """Scheduler Protocol decoupling node execution scheduling from ExecutionGraph topology."""
    scheduler_name: str

    def schedule(self, graph: ExecutionGraph, request: ExecutionRequest, engine: Any) -> ExecutionResult:
        ...


class SequentialScheduler:
    """Schedules and executes nodes sequentially following topological order."""
    scheduler_name: str = "SEQUENTIAL"

    def schedule(self, graph: ExecutionGraph, request: ExecutionRequest, engine: Any) -> ExecutionResult:
        ordered_nodes = graph.topological_sort()
        runtime_ctx = engine.create_runtime_context(request)

        state = ExecutionState(
            context=request.context,
            runtime=runtime_ctx,
            capability_id=request.capability_id,
            rendered_prompt=request.rendered_prompt,
        )

        trace_builder = ExecutionTraceBuilder(
            trace_id=request.context.trace_id,
            capability_id=request.capability_id,
            execution_id=request.context.execution_id,
        )

        executed_nodes = []
        for node in ordered_nodes:
            op = node.operation
            try:
                if hasattr(op, "before"):
                    state = op.before(state)
                if hasattr(op, "execute"):
                    state = op.execute(state)
                if hasattr(op, "after"):
                    state = op.after(state)
                executed_nodes.append(node)
            except Exception as exc:
                # Rollback/compensate in reverse order
                for n in reversed(executed_nodes):
                    try:
                        if hasattr(n.operation, "compensate"):
                            state = n.operation.compensate(state)
                        elif hasattr(n.operation, "rollback"):
                            state = n.operation.rollback(state)
                    except Exception:
                        pass
                raise exc

        for evt in state.trace_events:
            trace_builder.append(evt)

        trace = trace_builder.freeze()
        return ExecutionResult(capability_result=state.result, trace=trace)


class ParallelScheduler(SequentialScheduler):
    """Scheduler prepared for parallel branch execution (falls back to topological sequential)."""
    scheduler_name: str = "PARALLEL"
