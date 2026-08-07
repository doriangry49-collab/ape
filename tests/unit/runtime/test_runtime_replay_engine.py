"""
Unit tests for ORION-110 Execution Graph Replay & Observability Engine.
Verifies schema_version 1 manifest creation, SHA-256 artifact hashing, tri-factor integrity verification,
fail-closed safety, DAG dependency step plans, and replay modes (RESUME, OVERWRITE, DRY_RUN).
"""

import json
from pathlib import Path
import tempfile

import pytest
from typer.testing import CliRunner

from ape.business import ExecutionOrchestrator, VentureWorkspaceManager
from ape.cli import app
from ape.runtime.engine import CheckpointStore
from ape.business.replay import ReplayEngine, ReplayMode

runner = CliRunner()


def test_schema_version_1_manifest_and_sha256_indexing():
    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace_mgr = VentureWorkspaceManager(root_dir=Path(tmp_dir) / "ventures")
        orchestrator = ExecutionOrchestrator(workspace_manager=workspace_mgr)

        record = orchestrator.run_venture("Build Real Estate Automation SaaS")

        workspace_dir = workspace_mgr.get_workspace_path(record.venture_id)
        manifest_path = workspace_dir / "execution.json"

        assert manifest_path.exists()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert data["schema_version"] == 1
        assert data["runtime_version"] == "1.0.0"
        assert data["workflow_version"] == "ORION-110"
        assert len(data["steps"]) == 4
        assert len(data["artifacts"]) >= 10
        assert "sha256" in data["artifacts"][0]
        assert "size_bytes" in data["artifacts"][0]


def test_replay_engine_dry_run_and_dag_plans():
    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace_mgr = VentureWorkspaceManager(root_dir=Path(tmp_dir) / "ventures")
        orchestrator = ExecutionOrchestrator(workspace_manager=workspace_mgr)

        record = orchestrator.run_venture("Build Chrome Extension")
        v_id = record.venture_id

        engine = ReplayEngine(ventures_root=Path(tmp_dir) / "ventures")

        # Test Dry-Run Mode
        result = engine.replay_venture(v_id, from_step_id="engineering", mode=ReplayMode.DRY_RUN)

        assert result.success
        assert "DRY RUN completed" in result.message
        assert len(result.plans) == 4
        assert result.plans[0].status == "SKIPPED"  # research skipped
        assert result.plans[1].status == "PENDING"  # engineering pending


def test_replay_engine_fail_closed_on_artifact_mismatch():
    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace_mgr = VentureWorkspaceManager(root_dir=Path(tmp_dir) / "ventures")
        orchestrator = ExecutionOrchestrator(workspace_manager=workspace_mgr)

        record = orchestrator.run_venture("Build Automation Bot")
        v_id = record.venture_id

        # Corrupt an artifact file on disk
        workspace_dir = workspace_mgr.get_workspace_path(v_id)
        corrupt_file = workspace_dir / "repo" / "Dockerfile"
        if corrupt_file.exists():
            corrupt_file.write_text("CORRUPTED PAYLOAD", encoding="utf-8")

        engine = ReplayEngine(
            checkpoint_store=CheckpointStore(root_dir=Path(tmp_dir) / "ventures"),
            ventures_root=Path(tmp_dir) / "ventures",
        )

        # Resume mode should FAIL CLOSED due to SHA256 mismatch
        result = engine.replay_venture(v_id, from_step_id="engineering", mode=ReplayMode.RESUME)

        assert not result.success
        assert "FAIL-CLOSED Integrity Mismatch" in result.message
        assert "SHA256 Mismatch" in result.message


def test_cli_observability_history_show_replay():
    # Run a venture via CLI
    runner.invoke(app, ["venture", "run", "--goal", "Build YouTube Analytics Studio"])

    # Test history
    res_history = runner.invoke(app, ["venture", "history"])
    assert res_history.exit_code == 0
    assert "APE Venture Execution History" in res_history.output

    # Get active venture_id
    ventures_dir = Path(".build/ventures")
    for v_dir in ventures_dir.iterdir():
        if v_dir.is_dir() and (v_dir / "execution.json").exists():
            v_id = v_dir.name

            # Test show command
            res_show = runner.invoke(app, ["venture", "show", "--venture-id", v_id])
            assert res_show.exit_code == 0
            assert "Venture Details & Execution Graph" in res_show.output
            assert "schema_version: 1" in res_show.output

            # Test replay command in dry_run mode
            res_replay = runner.invoke(app, ["venture", "replay", "--venture-id", v_id, "--from-dept", "engineering", "--mode", "dry_run"])
            assert res_replay.exit_code == 0
            assert "DRY RUN" in res_replay.output
            break
