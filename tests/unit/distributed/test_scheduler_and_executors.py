"""
Unit tests for DistributedScheduler and Worker Executors (EPIC-10A / EPIC-10B).
"""

import pytest

from ape.distributed.executors import DockerExecutor, LocalExecutor
from ape.distributed.queue import DistributedQueue
from ape.distributed.registry import WorkerRegistry
from ape.distributed.scheduler import DistributedScheduler


def test_distributed_scheduler_dispatch():
    registry = WorkerRegistry()
    registry.register_worker("w_01", "node1", "cpu")

    queue = DistributedQueue()
    queue.push("t_01", "calc_app", "compile_task", priority=1)

    scheduler = DistributedScheduler(registry=registry, queue=queue)
    dispatch_res = scheduler.dispatch_next()

    assert dispatch_res is not None
    assert dispatch_res["status"] == "DISPATCHED"
    assert dispatch_res["worker_id"] == "w_01"


def test_executors_execution():
    local_exec = LocalExecutor()
    assert local_exec.health_check() is True
    res1 = local_exec.execute({"task_id": "t_local"})
    assert res1["status"] == "COMPLETED"

    docker_exec = DockerExecutor()
    assert docker_exec.health_check() is True
    res2 = docker_exec.execute({"task_id": "t_docker"})
    assert res2["status"] == "COMPLETED"
