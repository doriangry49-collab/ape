"""
ExecutionEventStore & Materialized MemorySnapshot — ORION-115 Specification.
Defines StateEvent, ExecutionEventStore, and materialized MemorySnapshot for audit, replay, and simulation.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class StateEvent:
    """Immutable state transformation event for event sourcing."""
    event_id: str
    key: str
    value: Any
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True)
class MemorySnapshot:
    """Immutable materialized memory snapshot generated from ExecutionEventStore."""
    snapshot_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    event_count: int = 0

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)


class ExecutionEventStore:
    """Stores immutable state transformation events and materializes MemorySnapshots."""

    def __init__(self, trace_id: str) -> None:
        self.trace_id = trace_id
        self._events: List[StateEvent] = []

    def append(self, key: str, value: Any) -> StateEvent:
        evt = StateEvent(
            event_id=f"evt_{len(self._events) + 1}",
            key=key,
            value=value,
        )
        self._events.append(evt)
        return evt

    def list_events(self) -> List[StateEvent]:
        return list(self._events)

    def materialize(self) -> MemorySnapshot:
        """Materialize current StateEvents into an immutable MemorySnapshot."""
        merged: Dict[str, Any] = {}
        for evt in self._events:
            merged[evt.key] = evt.value

        return MemorySnapshot(
            snapshot_id=f"snap_{self.trace_id}_{len(self._events)}",
            data=merged,
            event_count=len(self._events),
        )
