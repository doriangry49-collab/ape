"""
Worker Registry — RFC-022 / EPIC-10A Specification.
Manages registration, slot capacity, and heartbeat tracking for worker nodes (CPU, GPU, Docker, K8s).
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional
from ape.distributed.contracts import WorkerInfo


class WorkerRegistry:
    """Registry tracking active, busy, and offline worker nodes."""

    def __init__(self, heartbeat_timeout: float = 30.0) -> None:
        self.heartbeat_timeout = heartbeat_timeout
        self._workers: Dict[str, WorkerInfo] = {}

    def register_worker(self, worker_id: str, hostname: str, node_type: str = "cpu", capabilities: Optional[List[str]] = None, max_slots: int = 4) -> WorkerInfo:
        """Register or update a worker node."""
        worker = WorkerInfo(
            worker_id=worker_id,
            hostname=hostname,
            node_type=node_type,
            capabilities=capabilities or ["python", "pytest"],
            max_slots=max_slots,
            active_slots=0,
            status="ONLINE",
            last_heartbeat=time.time(),
        )
        self._workers[worker_id] = worker
        return worker

    def heartbeat(self, worker_id: str) -> bool:
        """Record heartbeat pulse from a worker node."""
        if worker_id in self._workers:
            self._workers[worker_id].last_heartbeat = time.time()
            if self._workers[worker_id].status == "OFFLINE":
                self._workers[worker_id].status = "ONLINE"
            return True
        return False

    def list_available_workers(self) -> List[WorkerInfo]:
        """Return list of online workers with free capacity slots."""
        now = time.time()
        available: List[WorkerInfo] = []

        for w in self._workers.values():
            if (now - w.last_heartbeat) > self.heartbeat_timeout:
                w.status = "OFFLINE"
                continue
            if w.status != "OFFLINE" and w.active_slots < w.max_slots:
                available.append(w)

        return available

    def get_worker(self, worker_id: str) -> Optional[WorkerInfo]:
        """Fetch worker info by ID."""
        return self._workers.get(worker_id)

    def list_all_workers(self) -> List[WorkerInfo]:
        """Return all registered worker nodes."""
        return list(self._workers.values())


# Global default worker registry instance
default_worker_registry = WorkerRegistry()


def get_default_worker_registry() -> WorkerRegistry:
    """Returns global default worker registry instance."""
    return default_worker_registry
