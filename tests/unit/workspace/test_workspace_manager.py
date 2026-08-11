"""
Unit tests for WorkspaceManager (PR-W1).
"""

from pathlib import Path

from ape.workspace.manager import WorkspaceManager


def test_workspace_manager_lifecycle(tmp_path: Path):
    mgr = WorkspaceManager(tmp_path)

    # 1. Create workspace
    ctx1 = mgr.create_workspace("Customer A", description="Production Tenant A")
    assert ctx1.slug == "customer_a"
    assert (tmp_path / ".workspaces" / "customer_a").exists()

    # 2. Switch workspace
    switched = mgr.switch_workspace("customer_a")
    assert switched.active is True
    assert mgr.get_active_workspace().slug == "customer_a"

    # 3. List workspaces
    workspaces = mgr.list_workspaces()
    assert len(workspaces) >= 1
    assert any(ws.slug == "customer_a" for ws in workspaces)

    # 4. Archive workspace
    archived = mgr.archive_workspace("customer_a")
    assert archived is True
    assert (tmp_path / ".workspaces" / "customer_a.archived").exists()
