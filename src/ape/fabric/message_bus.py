"""
In-Memory SwarmMessageBus & SwarmMessage — ORION-116 Specification.
Provides synchronous in-memory pub/sub message bus for inter-agent communication.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass(frozen=True)
class SwarmMessage:
    """Immutable inter-agent message payload broadcast over SwarmMessageBus."""
    message_id: str
    sender_id: str
    recipient_id: str
    topic: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class SwarmMessageBus:
    """Synchronous in-memory message bus routing inter-agent messages within a single process."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[SwarmMessage], None]]] = {}
        self._history: List[SwarmMessage] = []

    def subscribe(self, topic: str, handler: Callable[[SwarmMessage], None]) -> None:
        """Subscribe a handler callback to a specific topic."""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(handler)

    def publish(self, message: SwarmMessage) -> None:
        """Publish a message to all subscribed topic handlers."""
        self._history.append(message)
        handlers = self._subscribers.get(message.topic, [])
        for h in handlers:
            try:
                h(message)
            except Exception:
                pass

    def get_history(self, topic: Optional[str] = None) -> List[SwarmMessage]:
        """Return published message history filtered by topic."""
        if topic:
            return [m for m in self._history if m.topic == topic]
        return list(self._history)
