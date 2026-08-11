"""
Observation Bus & Event System — RFC-022 / PR-A5 Specification.
Thread-safe Pub/Sub Event Bus for real-time Fabric Agent notifications and dashboard state updates.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass
class FabricEvent:
    """Event payload dispatched through ObservationBus."""
    event_type: str
    source_agent: str
    topic_slug: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "source_agent": self.source_agent,
            "topic_slug": self.topic_slug,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class ObservationBus:
    """Thread-safe Pub/Sub Observation Bus for Fabric Agents."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[FabricEvent], None]]] = {}
        self._history: List[FabricEvent] = []

    def subscribe(self, event_type: str, handler: Callable[[FabricEvent], None]) -> None:
        """Subscribe a handler callback to a specific event_type or '*' for all events."""
        key = event_type.strip().lower()
        if key not in self._subscribers:
            self._subscribers[key] = []
        self._subscribers[key].append(handler)

    def publish(self, event: FabricEvent) -> None:
        """Publish an event to all matching subscribers."""
        self._history.append(event)
        key = event.event_type.strip().lower()

        # Notify specific handlers
        for handler in self._subscribers.get(key, []):
            try:
                handler(event)
            except Exception:
                pass

        # Notify wildcard handlers
        for handler in self._subscribers.get("*", []):
            try:
                handler(event)
            except Exception:
                pass

    def get_history(self, event_type: Optional[str] = None) -> List[FabricEvent]:
        """Return event history optionally filtered by event_type."""
        if not event_type:
            return list(self._history)
        key = event_type.strip().lower()
        return [e for e in self._history if e.event_type.strip().lower() == key]


# Global default observation bus instance
default_observation_bus = ObservationBus()


def get_default_observation_bus() -> ObservationBus:
    """Returns global default observation bus instance."""
    return default_observation_bus
