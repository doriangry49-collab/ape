"""
RFC-018 ReleaseGate Unit and Governance Tests.
(RFC-018)
"""
import json
import subprocess

import pytest

from ape.intelligence.execution.models import (
    ExecutionState,
    ExecutionStatus,
    ExecutionTask,
    TaskStatus,
)
from ape.intelligence.execution.release import ReleaseGate
from ape.utils import get_artifact_history


@pytest.fixture
def setup_git_workspace(tmp_path):
    workspace = tmp_path / "git_workspace"
    workspace.mkdir()

    # Initialize dummy git repository
    subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "APE Agent"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.email", "agent@ape.dev"], cwd=workspace, check=True)

    # Initial commit so git HEAD exists
    readme = workspace / "README.md"
    readme.write_text("# APE Workspace")
    subprocess.run(["git", "add", "README.md"], cwd=workspace, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=workspace, check=True)

    # Create ExecutionState artifact
    state_dir = workspace / ".build" / "execution" / "test_calc"
    state_dir.mkdir(parents=True)
    state_file = state_dir / "current.json"

    state = ExecutionState(
        execution_id="exec_test_018",
        roadmap_id="rm_test_018",
        topic="Calculator App",
        tasks=[
            ExecutionTask(
                task_id="t1",
                description="Build calc",
                deliverables=["calc.py"],
                action="create_file",
                status=TaskStatus.COMPLETED
            )
        ],
        decision_id="dec_test_018",
        policy_decision="BUILD",
        evidence_hash="hash_test_018",
        status=ExecutionStatus.COMPLETED
    )
    state_file.write_text(json.dumps(state.to_dict(), indent=2))

    return workspace


def test_release_gate_happy_path(setup_git_workspace):
    workspace = setup_git_workspace

    # Create new file in workspace
    calc_file = workspace / "calc.py"
    calc_file.write_text("def add(a, b):\n    return a + b\n")

    gate = ReleaseGate(workspace)
    proposal = gate.prepare_release("test_calc")

    assert proposal.quality_check_passed is True
    assert "dec_test_018" in proposal.commit_message
    assert "BUILD" in proposal.commit_message
    assert "hash_test_018" in proposal.commit_message
    assert "calc.py" in proposal.changed_files

    # Execute release with user approval
    success = gate.execute_release(proposal, user_approved=True)
    assert success is True

    # Verify git log contains commit with lineage
    git_log = subprocess.run(["git", "log", "-n", "1"], cwd=workspace, capture_output=True, text=True).stdout
    assert "feat(execution): [test_calc] complete execution exec_test_018" in git_log
    assert "Decision ID: dec_test_018" in git_log

    # Verify release evidence log
    evidence_dir = workspace / ".governance" / "evidence"
    release_log = get_artifact_history(evidence_dir, "release")
    assert release_log.exists()
    logs = [json.loads(line) for line in release_log.read_text().strip().split("\n") if line.strip()]
    assert len(logs) == 1
    assert logs[0]["status"] == "COMMITTED"
    assert logs[0]["decision_id"] == "dec_test_018"


def test_release_gate_user_denial(setup_git_workspace):
    workspace = setup_git_workspace
    calc_file = workspace / "calc.py"
    calc_file.write_text("def add(a, b):\n    return a + b\n")

    gate = ReleaseGate(workspace)
    proposal = gate.prepare_release("test_calc")

    # User denies approval
    success = gate.execute_release(proposal, user_approved=False)
    assert success is False

    # Verify git working tree remains untracked/unstaged
    status = subprocess.run(["git", "status", "--porcelain"], cwd=workspace, capture_output=True, text=True).stdout
    assert "?? calc.py" in status or "M calc.py" in status

    # Verify release evidence logs DENIED
    evidence_dir = workspace / ".governance" / "evidence"
    release_log = get_artifact_history(evidence_dir, "release")
    logs = [json.loads(line) for line in release_log.read_text().strip().split("\n") if line.strip()]
    assert logs[0]["status"] == "DENIED"


def test_release_gate_rejects_uncompleted_state(setup_git_workspace):
    workspace = setup_git_workspace

    # Update state to IN_PROGRESS
    state_file = workspace / ".build" / "execution" / "test_calc" / "current.json"
    state_data = json.loads(state_file.read_text())
    state_data["status"] = "IN_PROGRESS"
    state_file.write_text(json.dumps(state_data))

    gate = ReleaseGate(workspace)
    with pytest.raises(ValueError, match="is not COMPLETED"):
        gate.prepare_release("test_calc")


def test_release_gate_rejects_invalid_lineage(setup_git_workspace):
    workspace = setup_git_workspace

    # Update state policy_decision to WATCH
    state_file = workspace / ".build" / "execution" / "test_calc" / "current.json"
    state_data = json.loads(state_file.read_text())
    state_data["policy_decision"] = "WATCH"
    state_file.write_text(json.dumps(state_data))

    gate = ReleaseGate(workspace)
    with pytest.raises(ValueError, match="Only BUILD or VALIDATE executions may be released"):
        gate.prepare_release("test_calc")


def test_release_gate_syntax_quality_failure(setup_git_workspace):
    workspace = setup_git_workspace

    # Create file with python syntax error
    calc_file = workspace / "calc.py"
    calc_file.write_text("def broken_syntax(\n")

    gate = ReleaseGate(workspace)
    proposal = gate.prepare_release("test_calc")

    assert proposal.quality_check_passed is False
    assert len(proposal.quality_errors) > 0

    # Execute release should refuse to commit failing quality check
    success = gate.execute_release(proposal, user_approved=True)
    assert success is False
