"""
Distributed Kernel Contracts — RFC-022 / EPIC-10A Specification.
Defines WorkerInfo, TaskLease, and QueueItem schemas for Distributed APE Kernel.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional


@dataclass
class WorkerInfo:
    """Represents a registered worker node in Distributed APE Kernel."""
    worker_id: str
    hostname: str
    node_type: str  # cpu, gpu, docker, k8s, ssh
    capabilities: List[str] = field(default_factory=list)
    max_slots: int = 4
    active_slots: int = 0
    status: str = "ONLINE"  # ONLINE, BUSY, OFFLINE
    last_heartbeat: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "hostname": self.hostname,
            "node_type": self.node_type,
            "capabilities": self.capabilities,
            "max_slots": self.max_slots,
            "active_slots": self.active_slots,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat,
            "metadata": self.metadata,
        }


@dataclass
class TaskLease:
    """Represents a lease contract granted to a worker node for a task."""
    lease_id: str
    task_id: str
    worker_id: str
    topic_slug: str
    granted_at: float = field(default_factory=time.time)
    ttl_seconds: float = 30.0
    status: str = "ACTIVE"  # ACTIVE, EXPIRED, RELEASED

    def is_expired(self) -> bool:
        return (time.time() - self.granted_at) > self.ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lease_id": self.lease_id,
            "task_id": self.task_id,
            "worker_id": self.worker_id,
            "topic_slug": self.topic_slug,
            "granted_at": self.granted_at,
            "ttl_seconds": self.ttl_seconds,
            "status": self.status,
            "expired": self.is_expired(),
        }


@dataclass
class QueueItem:
    """Represents a task queued for execution in Distributed Task Queue."""
    task_id: str
    topic_slug: str
    action: str
    priority: int = 1  # 1 = highest
    payload: Dict[str, Any] = field(default_factory=dict)
    retries: int = 0
    max_retries: int = 3
    status: str = "QUEUED"  # QUEUED, LEASED, RUNNING, COMPLETED, FAILED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "topic_slug": self.topic_slug,
            "action": self.action,
            "priority": self.priority,
            "payload": self.payload,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "status": self.status,
        }
