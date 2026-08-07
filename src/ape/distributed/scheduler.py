"""
Distributed Scheduler & Orchestrator — RFC-022 / EPIC-10A Specification.
Dispatches tasks from priority queue to lease-validated worker nodes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from ape.distributed.contracts import TaskLease, WorkerInfo
from ape.distributed.lease import LeaseManager
from ape.distributed.queue import DistributedQueue
from ape.distributed.registry import WorkerRegistry, get_default_worker_registry


class DistributedScheduler:
    """Dispatches tasks from DistributedQueue to WorkerRegistry with Fail-Closed leases."""

    def __init__(
        self,
        registry: Optional[WorkerRegistry] = None,
        queue: Optional[DistributedQueue] = None,
        lease_manager: Optional[LeaseManager] = None,
    ) -> None:
        self.registry = registry or get_default_worker_registry()
        self.queue = queue or DistributedQueue()
        self.lease_manager = lease_manager or LeaseManager()

    def dispatch_next(self) -> Optional[Dict[str, Any]]:
        """Dispatch next priority task to an available worker node."""
        # 1. Reclaim expired leases for fail-closed recovery
        expired_leases = self.lease_manager.reclaim_expired_leases()
        for lease in expired_leases:
            self.queue.push(
                task_id=f"{lease.task_id}_retry",
                topic_slug=lease.topic_slug,
                action="retry_task",
                priority=1,
            )

        # 2. Check available workers
        workers = self.registry.list_available_workers()
        if not workers:
            return None

        # 3. Pop next queued task
        item = self.queue.pop_next()
        if not item:
            return None

        # 4. Assign slot and grant lease
        target_worker = workers[0]
        target_worker.active_slots += 1

        lease = self.lease_manager.grant_lease(
            task_id=item.task_id,
            worker_id=target_worker.worker_id,
            topic_slug=item.topic_slug,
        )

        return {
            "task_id": item.task_id,
            "worker_id": target_worker.worker_id,
            "lease_id": lease.lease_id,
            "status": "DISPATCHED",
        }

    def get_status(self) -> Dict[str, Any]:
        """Return system status summary of Distributed Scheduler."""
        workers = self.registry.list_all_workers()
        queued = self.queue.list_queued()
        return {
            "status": "ACTIVE",
            "total_workers": len(workers),
            "online_workers": len([w for w in workers if w.status == "ONLINE"]),
            "queued_tasks": len(queued),
        }
