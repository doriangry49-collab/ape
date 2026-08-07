"""
Event-Sourced ExecutionTrace & ExecutionTraceBuilder — ORION-114 / ORION-115 Specification.
Defines ExecutionTrace model and ExecutionTraceBuilder for immutable audit trace generation.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional

from ape.capabilities.resiliency.telemetry import RuntimeEvent


@dataclass(frozen=True)
class ExecutionTrace:
    """Immutable event-sourced execution trace for explainability, audit, and governance."""
    trace_id: str
    capability_id: str
    execution_id: str
    events: List[RuntimeEvent] = field(default_factory=list)
    duration_ms: float = 0.0

    def summary(self) -> Dict[str, Any]:
        """Generate human-readable summary report from event-sourced events."""
        event_types = [e.event_type for e in self.events]
        selected_provider = ""
        for e in self.events:
            if e.event_type == "ProviderSelected":
                selected_provider = e.provider_id

        return {
            "trace_id": self.trace_id,
            "capability_id": self.capability_id,
            "execution_id": self.execution_id,
            "total_events": len(self.events),
            "event_sequence": event_types,
            "selected_provider": selected_provider,
            "duration_ms": self.duration_ms,
        }


class ExecutionTraceBuilder:
    """Builder pattern constructing immutable ExecutionTrace instances from appended RuntimeEvent packets."""

    def __init__(self, trace_id: str, capability_id: str, execution_id: str) -> None:
        self.trace_id = trace_id
        self.capability_id = capability_id
        self.execution_id = execution_id
        self._events: List[RuntimeEvent] = []
        self._start_time: float = time.time()

    def append(self, event: RuntimeEvent) -> "ExecutionTraceBuilder":
        """Append a structural RuntimeEvent to trace sequence."""
        self._events.append(event)
        return self

    def freeze(self) -> ExecutionTrace:
        """Freeze and return immutable ExecutionTrace."""
        dur_ms = round((time.time() - self._start_time) * 1000.0, 2)
        return ExecutionTrace(
            trace_id=self.trace_id,
            capability_id=self.capability_id,
            execution_id=self.execution_id,
            events=list(self._events),
            duration_ms=dur_ms,
        )
