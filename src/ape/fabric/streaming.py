"""
Cloud Native Event Streaming Adapter — EPIC G6-3 Specification.
Provides StreamAdapter contract for Redis Streams and NATS event bus distribution.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List


@dataclass
class StreamEvent:
    """Standardized event packet broadcast across distributed event streams."""
    topic: str
    event_type: str
    payload: Dict[str, Any]
    timestamp: float


class EventStreamEngine:
    """Distributed event stream engine wrapping ObservationBus events."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[StreamEvent], None]]] = {}

    def subscribe(self, topic: str, callback: Callable[[StreamEvent], None]) -> None:
        """Subscribe to a stream topic."""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)

    def publish(self, event: StreamEvent) -> int:
        """Publish event to all subscribers listening on event topic."""
        subscribers = self._subscribers.get(event.topic, [])
        for sub in subscribers:
            try:
                sub(event)
            except Exception:
                pass
        return len(subscribers)
