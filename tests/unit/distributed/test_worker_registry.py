"""
Unit tests for WorkerRegistry (EPIC-10A).
"""

import time

from ape.distributed.registry import WorkerRegistry


def test_worker_registry_lifecycle():
    reg = WorkerRegistry(heartbeat_timeout=1.0)

    worker = reg.register_worker("w_01", "node1", "cpu", max_slots=4)
    assert worker.worker_id == "w_01"
    assert worker.status == "ONLINE"

    available = reg.list_available_workers()
    assert len(available) == 1

    # Record heartbeat pulse
    hb_success = reg.heartbeat("w_01")
    assert hb_success is True


def test_worker_heartbeat_timeout():
    reg = WorkerRegistry(heartbeat_timeout=0.1)
    reg.register_worker("w_02", "node2", "gpu")

    time.sleep(0.2)
    available = reg.list_available_workers()
    assert len(available) == 0  # Marked OFFLINE due to timeout
