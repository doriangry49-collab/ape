"""
End-to-End Golden Path Reference Workflows — Generation 7A / EPIC 7A-1 Specification.
Executes the full 14-subsystem production flow across real software production scenarios.
"""

from pathlib import Path

from ape.business import ExecutiveBoard
from ape.distributed import DistributedQueue, DistributedScheduler, WorkerRegistry
from ape.security import JWTAuthEngine, WorkspaceRBAC
from ape.store import StateStore
from ape.workspace import EnterpriseKnowledgeGraph, WorkspaceManager


def test_golden_path_full_production_flow(tmp_path: Path):
    """Executes the complete Golden Path production workflow across all platform subsystems."""
    # 1. Auth & RBAC
    auth = JWTAuthEngine()
    token = auth.create_token(sub="lead_dev", role="ADMIN", workspace_slug="golden_ws")
    claims = auth.decode_token(token)
    assert claims is not None
    rbac = WorkspaceRBAC()
    assert rbac.check_permission(claims.role, "write") is True

    # 2. Workspace OS
    wm = WorkspaceManager(tmp_path)
    ctx = wm.create_workspace("Golden Path REST API", "Reference workflow")

    # 3. Business OS & Executive Board
    board = ExecutiveBoard()
    directive = board.issue_directive("Produce Golden Path REST API")
    exec_res = board.execute_directive(directive, workspace_context=ctx)
    assert exec_res["status"] == "APPROVED"

    # 4. Agent Fabric & Distributed Scheduler
    registry = WorkerRegistry()
    registry.register_worker("w_01", "node1", "cpu")
    queue = DistributedQueue()
    queue.push("t_rest_api", ctx.slug, "build_rest_api", priority=1)

    scheduler = DistributedScheduler(registry=registry, queue=queue)
    dispatch_res = scheduler.dispatch_next()
    assert dispatch_res is not None
    assert dispatch_res["worker_id"] == "w_01"

    # 5. Quality OS & State Store
    sstore = StateStore(tmp_path)
    sstore.record_build_state(ctx.slug, "exec_001", "COMPLETED", {"confidence": 95.0})

    # 6. Enterprise Knowledge Graph Update
    kg = EnterpriseKnowledgeGraph(tmp_path)
    kg.add_node("golden_path", "REST API Deliverable", {"status": "RELEASED"})
    summary = kg.get_summary()

    assert summary["total_nodes"] == 1
