"""
Lease Manager — RFC-022 / EPIC-10A Specification.
Issues task leases with fail-closed expiration and automatic task recovery on worker failure.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional
from ape.distributed.contracts import TaskLease


class LeaseManager:
    """Manages task leases and fail-closed expiration recovery."""

    def __init__(self, default_ttl: float = 30.0) -> None:
        self.default_ttl = default_ttl
        self._leases: Dict[str, TaskLease] = {}

    def grant_lease(self, task_id: str, worker_id: str, topic_slug: str, ttl: Optional[float] = None) -> TaskLease:
        """Grant a task execution lease to a worker."""
        lease_id = f"lease_{task_id}_{worker_id}"
        lease = TaskLease(
            lease_id=lease_id,
            task_id=task_id,
            worker_id=worker_id,
            topic_slug=topic_slug,
            granted_at=time.time(),
            ttl_seconds=ttl or self.default_ttl,
            status="ACTIVE",
        )
        self._leases[lease_id] = lease
        return lease

    def release_lease(self, lease_id: str) -> bool:
        """Release a task lease upon completion."""
        if lease_id in self._leases:
            self._leases[lease_id].status = "RELEASED"
            return True
        return False

    def reclaim_expired_leases() -> List[TaskLease]:
        """Scan and reclaim expired leases for fail-closed task recovery."""

    def reclaim_expired_leases(self) -> List[TaskLease]:
        """Scan and reclaim expired leases for fail-closed task recovery."""
        expired: List[TaskLease] = []
        for lease in self._leases.values():
            if lease.status == "ACTIVE" and lease.is_expired():
                lease.status = "EXPIRED"
                expired.append(lease)
        return expired
