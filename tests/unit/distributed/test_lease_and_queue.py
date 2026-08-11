"""
Unit tests for LeaseManager and DistributedQueue (EPIC-10A).
"""

import time

from ape.distributed.lease import LeaseManager
from ape.distributed.queue import DistributedQueue


def test_distributed_queue_priority():
    q = DistributedQueue()
    q.push("t1", "calc_app", "build", priority=2)
    q.push("t2", "calc_app", "urgent_build", priority=1)

    next_item = q.pop_next()
    assert next_item is not None
    assert next_item.task_id == "t2"  # Priority 1 popped first


def test_lease_manager_expiration_recovery():
    lm = LeaseManager(default_ttl=0.1)
    lease = lm.grant_lease("t_01", "w_01", "calc_app")

    assert lease.status == "ACTIVE"
    time.sleep(0.2)
    assert lease.is_expired() is True

    expired = lm.reclaim_expired_leases()
    assert len(expired) == 1
    assert expired[0].status == "EXPIRED"
