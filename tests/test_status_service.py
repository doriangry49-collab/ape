"""
RFC-021 StatusService & CLI Status Command Unit Tests.
(RFC-021)
"""
import json

import pytest
from typer.testing import CliRunner

from ape.cli import app
from ape.project import Project
from ape.services.status_service import StatusService
from ape.utils import append_to_evidence

runner = CliRunner()


@pytest.fixture
def status_workspace(tmp_path):
    # Setup mock workspace with .build and .governance
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / ".ape").mkdir()
    (workspace / ".ape" / "config.toml").write_text("[workspace]\nname = 'test_ws'\n")

    build_dir = workspace / ".build"
    (build_dir / "research").mkdir(parents=True)
    (build_dir / "decisions").mkdir(parents=True)
    (build_dir / "roadmaps").mkdir(parents=True)
    (build_dir / "execution" / "calculator_app").mkdir(parents=True)

    evidence_dir = workspace / ".governance" / "evidence"
    evidence_dir.mkdir(parents=True)

    # 0. Research
    (build_dir / "research" / "calculator_app.json").write_text(json.dumps({
        "topic": "Calculator App",
        "recommended_action": "BUILD",
        "signals": {"confidence": 0.85},
        "metadata": {"research_id": "res_001"}
    }))

    # 1. Decision
    (build_dir / "decisions" / "calculator_app.json").write_text(json.dumps({
        "decision_id": "dec_001",
        "decision": "BUILD",
        "policy": "BUILD_NOW",
        "overall_score": 85,
        "rule_id": "RULE_GO_BUILD"
    }))

    # 2. Roadmap
    (build_dir / "roadmaps" / "calculator_app.json").write_text(json.dumps({
        "roadmap_id": "rm_001",
        "decision_id": "dec_001",
        "goal": "Build Calc",
        "milestones": [{"milestone_id": "m1", "tasks": [{"task_id": "t1"}, {"task_id": "t2"}]}]
    }))

    # 3. Execution
    (build_dir / "execution" / "calculator_app" / "current.json").write_text(json.dumps({
        "execution_id": "exec_001",
        "roadmap_id": "rm_001",
        "decision_id": "dec_001",
        "status": "COMPLETED",
        "policy_decision": "BUILD",
        "evidence_hash": "hash_123",
        "tasks": [{"task_id": "t1", "status": "COMPLETED"}, {"task_id": "t2", "status": "COMPLETED"}]
    }))

    # 4. Release evidence
    append_to_evidence(evidence_dir, "release", {
        "topic_slug": "calculator_app",
        "execution_id": "exec_001",
        "decision_id": "dec_001",
        "status": "COMMITTED",
        "details": "Commit 087aa49 created"
    })

    return workspace


def test_status_service_completed_pipeline(status_workspace):
    project = Project.load(status_workspace)
    service = StatusService(project)

    report = service.get_topic_status("Calculator App")

    assert report.slug == "calculator_app"
    assert report.topic == "Calculator App"
    assert report.overall_status == "COMMITTED"
    assert report.lineage_match is True
    assert report.research.status == "PASSED"
    assert report.decision.status == "BUILD"
    assert report.roadmap.status == "GENERATED"
    assert report.roadmap.details["task_count"] == 2
    assert report.execution.status == "COMPLETED"
    assert report.execution.details["completed_tasks"] == 2
    assert report.release.status == "COMMITTED"


def test_status_service_partial_pipeline(status_workspace):
    # Setup partial topic with decision only
    build_dir = status_workspace / ".build"
    (build_dir / "decisions" / "idea_app.json").write_text(json.dumps({
        "decision_id": "dec_002",
        "decision": "VALIDATE",
        "policy": "VALIDATE_WITH_USERS",
        "overall_score": 65
    }))

    project = Project.load(status_workspace)
    service = StatusService(project)

    report = service.get_topic_status("idea_app")

    assert report.slug == "idea_app"
    assert report.overall_status == "DECIDED"
    assert report.decision.status == "VALIDATE"
    assert report.roadmap.status == "NOT_STARTED"
    assert report.execution.status == "NOT_STARTED"
    assert report.release.status == "NOT_STARTED"


def test_status_service_list_all_topics(status_workspace):
    project = Project.load(status_workspace)
    service = StatusService(project)

    summaries = service.list_all_topics()
    assert len(summaries) >= 1
    assert any(s.slug == "calculator_app" for s in summaries)


def test_status_service_corrupted_json(status_workspace):
    # Write invalid JSON into decisions
    (status_workspace / ".build" / "decisions" / "corrupt_app.json").write_text("INVALID_JSON{{{")

    project = Project.load(status_workspace)
    service = StatusService(project)

    report = service.get_topic_status("corrupt_app")
    assert report.decision.status == "CORRUPTED"


def test_status_service_strict_read_only(status_workspace):
    project = Project.load(status_workspace)
    service = StatusService(project)

    # Take snapshot of files
    snapshot_before = set(status_workspace.rglob("*"))

    _ = service.get_topic_status("Calculator App")
    _ = service.list_all_topics()

    snapshot_after = set(status_workspace.rglob("*"))
    assert snapshot_before == snapshot_after


def test_status_service_lineage_mismatch(status_workspace):
    # Mismatch decision_id in execution
    exec_file = status_workspace / ".build" / "execution" / "calculator_app" / "current.json"
    data = json.loads(exec_file.read_text())
    data["decision_id"] = "dec_OLD_MISMATCH"
    exec_file.write_text(json.dumps(data))

    project = Project.load(status_workspace)
    service = StatusService(project)

    report = service.get_topic_status("calculator_app")
    assert report.lineage_match is False


def test_status_service_release_evidence_matching(status_workspace):
    project = Project.load(status_workspace)
    service = StatusService(project)

    report = service.get_topic_status("calculator_app")
    assert report.release.details["details"] == "Commit 087aa49 created"


def test_cli_status_command_single_topic(status_workspace, monkeypatch):
    monkeypatch.chdir(status_workspace)
    res = runner.invoke(app, ["status", "Calculator App"])

    assert res.exit_code == 0
    assert "APE Build Status: 'Calculator App'" in res.stdout
    assert "Overall Status   : COMMITTED" in res.stdout
    assert "[1] Decision Gate: BUILD" in res.stdout


def test_cli_status_command_all_topics(status_workspace, monkeypatch):
    monkeypatch.chdir(status_workspace)
    res = runner.invoke(app, ["status", "--all"])

    assert res.exit_code == 0
    assert "APE Build Workspace Topics Overview" in res.stdout
    assert "calculator_app" in res.stdout


def test_cli_status_command_topic_not_found(status_workspace, monkeypatch):
    monkeypatch.chdir(status_workspace)
    res = runner.invoke(app, ["status", "NonExistentTopic"])

    assert res.exit_code == 0
    assert "not found in workspace" in res.stdout


def test_status_service_handles_null_nested_fields(status_workspace):
    build_dir = status_workspace / ".build"

    # Research with null metadata and signals
    (build_dir / "research" / "null_app.json").write_text(json.dumps({
        "topic": "Null App",
        "recommended_action": "BUILD",
        "signals": None,
        "metadata": None
    }))

    # Roadmap with null milestones
    (build_dir / "roadmaps" / "null_app.json").write_text(json.dumps({
        "roadmap_id": "rm_null",
        "decision_id": "dec_null",
        "goal": "Null Goal",
        "milestones": None
    }))

    project = Project.load(status_workspace)
    service = StatusService(project)

    report = service.get_topic_status("null_app")
    assert report.research.status == "PASSED"
    assert report.research.details["research_id"] == "N/A"
    assert report.roadmap.status == "GENERATED"
    assert report.roadmap.details["milestone_count"] == 0
    assert report.roadmap.details["task_count"] == 0


def test_status_service_all_topics_utc_timestamp_z(status_workspace):
    project = Project.load(status_workspace)
    service = StatusService(project)

    summaries = service.list_all_topics()
    assert len(summaries) >= 1
    target = next(s for s in summaries if s.slug == "calculator_app")
    assert target.last_updated.endswith("Z")
