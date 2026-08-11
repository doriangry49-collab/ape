"""
Unit tests for ORION-108 ExecutionOrchestrator & Execution Manifest (execution.json).
Verifies pure workflow orchestration, dependency injection, lifecycle hooks, execution.json SSOT creation,
and CLI subcommand functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from typer.testing import CliRunner

from ape.business import (
    ExecutionOrchestrator,
    OrchestratorHooks,
    VentureWorkspaceManager,
)
from ape.cli import app

runner = CliRunner()


def test_execution_orchestrator_dependency_injection_and_manifest():
    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace_mgr = VentureWorkspaceManager(root_dir=Path(tmp_dir) / "ventures")
        orchestrator = ExecutionOrchestrator(workspace_manager=workspace_mgr)

        record = orchestrator.run_venture(
            goal_title="Reduce listing prep time for real estate agents",
            target_market="Real Estate Turkey",
        )

        assert record.venture_id.startswith("v_")
        assert record.status == "COMPLETED"
        assert record.business_hypothesis["confidence_score"] > 80.0
        assert Path(record.release_zip_path).exists()

        # Verify execution.json SSOT
        workspace_dir = workspace_mgr.get_workspace_path(record.venture_id)
        manifest_path = workspace_dir / "execution.json"
        assert manifest_path.exists()

        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest_data["goal"] == "Reduce listing prep time for real estate agents"
        assert manifest_data["status"] == "COMPLETED"
        assert len(manifest_data["written_artifacts"]) >= 10


def test_orchestrator_lifecycle_hooks():
    before_ws_mock = MagicMock()
    after_ws_mock = MagicMock()
    before_dept_mock = MagicMock()
    after_dept_mock = MagicMock()
    completed_mock = MagicMock()

    hooks = OrchestratorHooks(
        on_before_workspace=before_ws_mock,
        on_after_workspace=after_ws_mock,
        on_before_department=before_dept_mock,
        on_after_department=after_dept_mock,
        on_completed=completed_mock,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace_mgr = VentureWorkspaceManager(root_dir=Path(tmp_dir) / "ventures")
        orchestrator = ExecutionOrchestrator(workspace_manager=workspace_mgr, hooks=hooks)

        record = orchestrator.run_venture("Automate YouTube Studio Video Editing")

        assert before_ws_mock.called
        assert after_ws_mock.called
        assert before_dept_mock.call_count == 4  # Research, Engineering, Marketing, Publishing
        assert after_dept_mock.call_count == 4
        assert completed_mock.called


def test_cli_venture_subcommands():
    # Test venture run
    result_run = runner.invoke(app, ["venture", "run", "--goal", "Build SaaS Accounting Tool"])
    assert result_run.exit_code == 0
    assert "APE Execution Orchestrator — Venture Creation Completed" in result_run.output

    # Test venture list
    result_list = runner.invoke(app, ["venture", "list"])
    assert result_list.exit_code == 0
    assert "Build SaaS Accounting Tool" in result_list.output

    # Extract venture_id from list or manifest
    ventures_dir = Path(".build/ventures")
    for v_dir in ventures_dir.iterdir():
        if v_dir.is_dir() and (v_dir / "execution.json").exists():
            v_id = v_dir.name
            # Test venture status
            result_status = runner.invoke(app, ["venture", "status", "--venture-id", v_id])
            assert result_status.exit_code == 0
            assert "Venture Manifest" in result_status.output
            break
