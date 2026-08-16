"""
RFC-020 Execution Boundary Safety & Visibility Unit Tests.
(RFC-020)
"""
import json

import pytest

from ape.intelligence.execution.engine import ExecutionEngine
from ape.intelligence.execution.models import (
    ExecutionState,
    ExecutionStatus,
    ExecutionTask,
    TaskStatus,
)
from ape.intelligence.execution.policy import validate_path_containment
from ape.intelligence.execution.release import ReleaseGate


def test_path_containment_relative_traversal(tmp_path):
    is_valid, err_msg = validate_path_containment(tmp_path, "../file.py")
    assert is_valid is False
    assert "Path traversal rejected" in err_msg


def test_path_containment_deep_relative_traversal(tmp_path):
    is_valid, err_msg = validate_path_containment(tmp_path, "../../outside.txt")
    assert is_valid is False
    assert "Path traversal rejected" in err_msg


def test_path_containment_absolute_outside_path(tmp_path):
    outside_dir = tmp_path.parent / "outside_dir" / "file.py"
    is_valid, err_msg = validate_path_containment(tmp_path, outside_dir)
    assert is_valid is False
    assert "Path traversal rejected" in err_msg


def test_path_containment_valid_inside_path(tmp_path):
    valid_path = tmp_path / "src" / "new_module.py"
    is_valid, err_msg = validate_path_containment(tmp_path, valid_path)
    assert is_valid is True
    assert err_msg == ""


def test_path_containment_relative_inside_path(tmp_path):
    is_valid, err_msg = validate_path_containment(tmp_path, "src/new_module.py")
    assert is_valid is True
    assert err_msg == ""


def test_execution_engine_rejects_path_traversal_deliverable(tmp_path, monkeypatch):
    # Setup minimal decision and roadmap artifacts
    slug = "test_traversal"
    build_dir = tmp_path / ".build"
    (build_dir / "decisions").mkdir(parents=True)
    (build_dir / "roadmaps").mkdir(parents=True)

    (build_dir / "decisions" / f"{slug}.json").write_text(
        json.dumps({"decision": "BUILD", "policy": "BUILD_NOW", "decision_id": "dec_trav"})
    )
    (build_dir / "roadmaps" / f"{slug}.json").write_text(
        json.dumps({
            "roadmap_id": "rm_trav",
            "decision_id": "dec_trav",
            "milestones": [
                {
                    "milestone_id": "m1",
                    "title": "M1",
                    "tasks": [
                        {
                            "task_id": "t1",
                            "description": "Create bad file",
                            "deliverables": ["../bad_file.py"],
                            "action": "create_file"
                        }
                    ]
                }
            ]
        })
    )

    engine = ExecutionEngine(tmp_path, dry_run=True)
    res = engine.execute("Test Traversal", slug)

    # Task should not be executed; state should reflect FAILED with path traversal error
    state_file = build_dir / "execution" / slug / "current.json"
    assert state_file.exists()
    state_data = json.loads(state_file.read_text())
    assert state_data["tasks"][0]["status"] == "FAILED"
    assert "Path traversal rejected" in state_data["tasks"][0]["error"]


def test_agent_wiring_failure_visibility_redacts_api_key(tmp_path, monkeypatch):
    # Set fake API key in environment
    secret_key = "sk-proj-SECRET1234567890KEY"
    monkeypatch.setenv("APE_PLANNER_API_KEY", secret_key)
    monkeypatch.setenv("APE_PLANNER_MODEL", "gpt-4o")

    # Pass an unresolvable base_url or monkeypatch provider to trigger an init exception
    monkeypatch.setenv("APE_PLANNER_BASE_URL", "http://invalid-dns-domain-that-does-not-exist-12345.local")

    engine = ExecutionEngine(tmp_path, dry_run=True)
    # The agent should fail to initialize gracefully with agent_init_error populated
    # And the secret key must NEVER be leaked in the error message
    if engine.agent_init_error:
        assert secret_key not in engine.agent_init_error


def test_release_gate_git_failure_visibility_fails_closed(tmp_path):
    # Non-git workspace directory (no .git repo initialized)
    workspace = tmp_path / "non_git_workspace"
    workspace.mkdir()

    # Create ExecutionState artifact
    state_dir = workspace / ".build" / "execution" / "test_slug"
    state_dir.mkdir(parents=True)
    state_file = state_dir / "current.json"

    state = ExecutionState(
        execution_id="exec_test_git_fail",
        roadmap_id="rm_test",
        topic="Test Topic",
        tasks=[
            ExecutionTask(
                task_id="t1",
                description="Task 1",
                deliverables=["file.py"],
                action="create_file",
                status=TaskStatus.COMPLETED
            )
        ],
        decision_id="dec_test",
        policy_decision="BUILD",
        evidence_hash="hash_test",
        status=ExecutionStatus.COMPLETED
    )
    state_file.write_text(json.dumps(state.to_dict()))

    gate = ReleaseGate(workspace)
    # Failure in git status --porcelain must raise RuntimeError, failing closed
    with pytest.raises(RuntimeError, match="Git status inspection failed"):
        gate.prepare_release("test_slug")


def test_path_containment_sibling_prefix_directory(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    sibling_evil_dir = tmp_path / "repo_evil" / "file.py"

    is_valid, err_msg = validate_path_containment(repo_dir, sibling_evil_dir)
    assert is_valid is False
    assert "Path traversal rejected" in err_msg


def test_agent_workspace_root_override(tmp_path):
    from ape.intelligence.execution.agent import ApeCoderAgent
    from ape.intelligence.roadmap.llm import PlannerModel

    class DummyLLM(PlannerModel):
        def generate(self, prompt: str, system_message: str, schema: dict) -> dict:
            return {
                "thought": "Create file outside root",
                "action": "create_file",
                "params": {
                    "path": "../../outside.py",
                    "content": "print('malicious outside content')"
                }
            }

    agent = ApeCoderAgent(model=DummyLLM())
    task = ExecutionTask(
        task_id="t1",
        description="Test agent workspace root",
        deliverables=["file.py"],
        action="create_file"
    )

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    res = agent.execute_task(task, workspace_root=repo_dir)
    assert len(res.steps) == 3
    assert res.steps[0].status == "REJECTED"
    assert "Path traversal rejected" in res.steps[0].stderr
