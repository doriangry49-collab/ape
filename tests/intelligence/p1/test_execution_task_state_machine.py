import json
import pytest
from pathlib import Path

from ape.intelligence.execution.models import (
    ExecutionState,
    ExecutionTask,
    TaskStatus,
)
from ape.intelligence.execution.state import (
    InvalidTransitionError,
    TaskStateMachine,
)
from ape.intelligence.execution.engine import ExecutionEngine, _infer_action


def test_task_status_denied_enum_exists():
    """Assert TaskStatus.DENIED enum value exists."""
    assert TaskStatus.DENIED == "DENIED"
    assert TaskStatus.DENIED.value == "DENIED"


def test_requires_approval_to_denied_transition():
    """Assert REQUIRES_APPROVAL -> DENIED works via deny()."""
    task = ExecutionTask(
        task_id="t1",
        description="Deploy to production",
        deliverables=[],
        action="deploy",
        status=TaskStatus.REQUIRES_APPROVAL,
    )
    sm = TaskStateMachine(task)
    sm.deny(reason="User rejected deployment")
    assert task.status == TaskStatus.DENIED
    assert task.error == "User rejected deployment"


def test_denied_to_in_progress_raises_invalid_transition():
    """Assert DENIED -> IN_PROGRESS raises InvalidTransitionError."""
    task = ExecutionTask(
        task_id="t1",
        description="Deploy task",
        deliverables=[],
        status=TaskStatus.DENIED,
    )
    sm = TaskStateMachine(task)
    with pytest.raises(InvalidTransitionError):
        sm.start()


def test_denied_to_completed_raises_invalid_transition():
    """Assert DENIED -> COMPLETED raises InvalidTransitionError."""
    task = ExecutionTask(
        task_id="t1",
        description="Deploy task",
        deliverables=[],
        status=TaskStatus.DENIED,
    )
    sm = TaskStateMachine(task)
    with pytest.raises(InvalidTransitionError):
        sm.complete()


def test_denied_is_terminal():
    """Assert DENIED is terminal and rejects all transitions."""
    task = ExecutionTask(
        task_id="t1",
        description="Deploy task",
        deliverables=[],
        status=TaskStatus.DENIED,
    )
    sm = TaskStateMachine(task)
    with pytest.raises(InvalidTransitionError):
        sm.start()
    with pytest.raises(InvalidTransitionError):
        sm.complete()
    with pytest.raises(InvalidTransitionError):
        sm.fail()
    with pytest.raises(InvalidTransitionError):
        sm.retry()


def test_completed_is_terminal():
    """Assert COMPLETED is terminal and rejects invalid transitions."""
    task = ExecutionTask(
        task_id="t1",
        description="Build task",
        deliverables=[],
        status=TaskStatus.COMPLETED,
    )
    sm = TaskStateMachine(task)
    with pytest.raises(InvalidTransitionError):
        sm.start()


def test_blocked_is_terminal():
    """Assert BLOCKED is terminal and rejects invalid transitions."""
    task = ExecutionTask(
        task_id="t1",
        description="Docker task",
        deliverables=[],
        status=TaskStatus.BLOCKED,
    )
    sm = TaskStateMachine(task)
    with pytest.raises(InvalidTransitionError):
        sm.start()


def test_failed_to_in_progress_via_retry():
    """Assert FAILED -> IN_PROGRESS via retry() works."""
    task = ExecutionTask(
        task_id="t1",
        description="Failed task",
        deliverables=[],
        status=TaskStatus.FAILED,
    )
    sm = TaskStateMachine(task)
    sm.retry()
    assert task.status == TaskStatus.IN_PROGRESS


def test_paused_to_in_progress_via_resume():
    """Assert PAUSED -> IN_PROGRESS via resume() works."""
    task = ExecutionTask(
        task_id="t1",
        description="Paused task",
        deliverables=[],
        status=TaskStatus.PAUSED,
    )
    sm = TaskStateMachine(task)
    sm.resume()
    assert task.status == TaskStatus.IN_PROGRESS


def test_requires_approval_to_in_progress_via_approve():
    """Assert REQUIRES_APPROVAL -> IN_PROGRESS via approve() works."""
    task = ExecutionTask(
        task_id="t1",
        description="Deployment task",
        deliverables=[],
        status=TaskStatus.REQUIRES_APPROVAL,
    )
    sm = TaskStateMachine(task)
    sm.approve()
    assert task.status == TaskStatus.IN_PROGRESS


def test_explicit_action_not_overridden_by_infer_action():
    """Assert explicit task.action is preserved and not overridden."""
    task_action = "git_commit"
    # Even if description matches 'delete', explicit action 'git_commit' wins
    inferred = _infer_action("delete all files")
    assert inferred == "delete_file"

    task = ExecutionTask(
        task_id="t1",
        description="delete all files",
        deliverables=[],
        action=task_action,
    )
    assert task.action == "git_commit"


def test_denial_event_preserves_decision_lineage(tmp_path: Path):
    """Assert denial event in execution.jsonl carries decision_id, policy_decision, and evidence_hash."""
    from datetime import datetime, timezone

    slug = "denial-lineage-test"
    decisions_dir = tmp_path / ".build" / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)

    decision_data = {
        "decision_id": "dec_denial_999",
        "decision": "BUILD",
        "policy": "BUILD_NOW",
        "evidence_hash": "hash_denial_abc",
        "overall_score": 80,
    }
    (decisions_dir / f"{slug}.json").write_text(json.dumps(decision_data), encoding="utf-8")

    roadmaps_dir = tmp_path / ".build" / "roadmaps"
    roadmaps_dir.mkdir(parents=True, exist_ok=True)
    roadmap_data = {
        "roadmap_id": f"rm_{slug}",
        "decision_id": "dec_denial_999",
        "policy_decision": "BUILD",
        "milestones": [
            {
                "milestone_id": "ms_1",
                "title": "Deploy Phase",
                "tasks": [
                    {
                        "task_id": "tsk_deploy_1",
                        "description": "Deploy to production server",
                        "deliverables": [],
                        "action": "deploy",
                    }
                ],
            }
        ],
    }
    (roadmaps_dir / f"{slug}.json").write_text(json.dumps(roadmap_data), encoding="utf-8")

    engine = ExecutionEngine(tmp_path, dry_run=True, auto_deny_approvals=True)
    engine.execute("Denial Lineage Test", slug)

    # Check saved execution state has task in DENIED status
    state_file = tmp_path / ".build" / "execution" / slug / "current.json"
    assert state_file.exists()
    state_dict = json.loads(state_file.read_text(encoding="utf-8"))
    assert state_dict["tasks"][0]["status"] == "DENIED"

    # Check evidence log contains DENIED event with complete lineage
    partition = datetime.now(timezone.utc).strftime("%Y-%m")
    log_file = tmp_path / ".governance" / "evidence" / f"execution-{partition}.jsonl"
    assert log_file.exists()

    events = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    denied_events = [e for e in events if e.get("event") == "DENIED"]
    assert len(denied_events) >= 1

    denied_event = denied_events[0]
    assert denied_event["decision_id"] == "dec_denial_999"
    assert denied_event["policy_decision"] == "BUILD"
    assert denied_event["evidence_hash"] == "hash_denial_abc"
