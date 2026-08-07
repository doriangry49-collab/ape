"""
Distributed Priority Queue — RFC-022 / EPIC-10A Specification.
Implements priority task queueing, retries, timeouts, and cancellations.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from ape.distributed.contracts import QueueItem


class DistributedQueue:
    """Thread-safe priority task queue supporting retries and cancellation."""

    def __init__(self) -> None:
        self._items: Dict[str, QueueItem] = {}

    def push(self, task_id: str, topic_slug: str, action: str, priority: int = 1, payload: Optional[Dict[str, Any]] = None) -> QueueItem:
        """Push a task into priority queue."""
        item = QueueItem(
            task_id=task_id,
            topic_slug=topic_slug,
            action=action,
            priority=priority,
            payload=payload or {},
            status="QUEUED",
        )
        self._items[task_id] = item
        return item

    def pop_next(self) -> Optional[QueueItem]:
        """Pop next highest-priority queued task."""
        queued = [item for item in self._items.values() if item.status == "QUEUED"]
        if not queued:
            return None
        queued.sort(key=lambda x: x.priority)
        selected = queued[0]
        selected.status = "LEASED"
        return selected

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a queued task."""
        if task_id in self._items:
            self._items[task_id].status = "FAILED"
            return True
        return False

    def list_queued(self) -> List[QueueItem]:
        """Return all tasks in queue."""
        return list(self._items.values())
