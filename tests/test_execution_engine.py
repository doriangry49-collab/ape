"""
RFC-007: Execution Engine — TDD RED Phase
All tests here are written BEFORE implementation (RED phase).
"""
from __future__ import annotations

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# ExecutionPolicy tests
# ---------------------------------------------------------------------------

class TestExecutionPolicy:
    def _policy(self):
        from ape.intelligence.execution.policy import ExecutionPolicy
        return ExecutionPolicy()

    def test_read_file_is_safe(self):
        policy = self._policy()
        assert policy.classify("read_file") == "SAFE"

    def test_run_tests_is_safe(self):
        policy = self._policy()
        assert policy.classify("run_tests") == "SAFE"

    def test_create_new_file_is_safe(self):
        policy = self._policy()
        assert policy.classify("create_file") == "SAFE"

    def test_git_diff_is_safe(self):
        policy = self._policy()
        assert policy.classify("git_diff") == "SAFE"

    def test_modify_existing_file_requires_approval(self):
        policy = self._policy()
        assert policy.classify("modify_file") == "REQUIRES_APPROVAL"

    def test_git_commit_requires_approval(self):
        policy = self._policy()
        assert policy.classify("git_commit") == "REQUIRES_APPROVAL"

    def test_git_push_requires_approval(self):
        policy = self._policy()
        assert policy.classify("git_push") == "REQUIRES_APPROVAL"

    def test_delete_file_requires_approval(self):
        policy = self._policy()
        assert policy.classify("delete_file") == "REQUIRES_APPROVAL"

    def test_deploy_requires_approval(self):
        policy = self._policy()
        assert policy.classify("deploy") == "REQUIRES_APPROVAL"

    def test_credential_exposure_is_forbidden(self):
        policy = self._policy()
        assert policy.classify("credential_exposure") == "FORBIDDEN"

    def test_external_api_write_requires_approval(self):
        policy = self._policy()
        assert policy.classify("external_api_write") == "REQUIRES_APPROVAL"

    def test_unknown_action_defaults_to_requires_approval(self):
        """Unknown actions should never be auto-executed."""
        policy = self._policy()
        assert policy.classify("unknown_random_action") == "REQUIRES_APPROVAL"


# ---------------------------------------------------------------------------
# State Machine tests
# ---------------------------------------------------------------------------

class TestTaskStateMachine:
    def _make_task(self, task_id="tsk_1", action="create_file"):
        from ape.intelligence.execution.models import ExecutionTask
        return ExecutionTask(
            task_id=task_id,
            description="Test task",
            action=action,
            deliverables=[]
        )

    def test_initial_status_is_pending(self):
        task = self._make_task()
        from ape.intelligence.execution.models import TaskStatus
        assert task.status == TaskStatus.PENDING

    def test_pending_to_in_progress(self):
        from ape.intelligence.execution.models import TaskStatus
        from ape.intelligence.execution.state import TaskStateMachine
        task = self._make_task()
        sm = TaskStateMachine(task)
        sm.start()
        assert task.status == TaskStatus.IN_PROGRESS

    def test_in_progress_to_completed(self):
        from ape.intelligence.execution.models import TaskStatus
        from ape.intelligence.execution.state import TaskStateMachine
        task = self._make_task()
        sm = TaskStateMachine(task)
        sm.start()
        sm.complete()
        assert task.status == TaskStatus.COMPLETED

    def test_in_progress_to_failed(self):
        from ape.intelligence.execution.models import TaskStatus
        from ape.intelligence.execution.state import TaskStateMachine
        task = self._make_task()
        sm = TaskStateMachine(task)
        sm.start()
        sm.fail(error="Something broke")
        assert task.status == TaskStatus.FAILED
        assert task.error == "Something broke"

    def test_failed_to_in_progress_via_retry(self):
        from ape.intelligence.execution.models import TaskStatus
        from ape.intelligence.execution.state import TaskStateMachine
        task = self._make_task()
        sm = TaskStateMachine(task)
        sm.start()
        sm.fail(error="err")
        sm.retry()
        assert task.status == TaskStatus.IN_PROGRESS

    def test_in_progress_to_paused(self):
        from ape.intelligence.execution.models import TaskStatus
        from ape.intelligence.execution.state import TaskStateMachine
        task = self._make_task()
        sm = TaskStateMachine(task)
        sm.start()
        sm.pause()
        assert task.status == TaskStatus.PAUSED

    def test_paused_to_in_progress_via_resume(self):
        from ape.intelligence.execution.models import TaskStatus
        from ape.intelligence.execution.state import TaskStateMachine
        task = self._make_task()
        sm = TaskStateMachine(task)
        sm.start()
        sm.pause()
        sm.resume()
        assert task.status == TaskStatus.IN_PROGRESS

    def test_pending_to_requires_approval(self):
        from ape.intelligence.execution.models import TaskStatus
        from ape.intelligence.execution.state import TaskStateMachine
        task = self._make_task(action="modify_file")
        sm = TaskStateMachine(task)
        sm.request_approval()
        assert task.status == TaskStatus.REQUIRES_APPROVAL

    def test_requires_approval_to_in_progress_on_yes(self):
        from ape.intelligence.execution.models import TaskStatus
        from ape.intelligence.execution.state import TaskStateMachine
        task = self._make_task(action="modify_file")
        sm = TaskStateMachine(task)
        sm.request_approval()
        sm.approve()
        assert task.status == TaskStatus.IN_PROGRESS

    def test_requires_approval_stays_on_no(self):
        from ape.intelligence.execution.models import TaskStatus
        from ape.intelligence.execution.state import TaskStateMachine
        task = self._make_task(action="modify_file")
        sm = TaskStateMachine(task)
        sm.request_approval()
        sm.deny()
        assert task.status == TaskStatus.REQUIRES_APPROVAL


# ---------------------------------------------------------------------------
# Resume semantics
# ---------------------------------------------------------------------------

class TestResumeSemantics:
    def _make_execution_state(self, tmp_path, statuses: dict) -> Path:
        tasks = []
        for tid, status in statuses.items():
            tasks.append({
                "task_id": tid,
                "description": f"Task {tid}",
                "action": "create_file",
                "deliverables": [],
                "status": status.value if hasattr(status, "value") else status,
                "error": None
            })
        state = {
            "execution_id": "exec_test01",
            "roadmap_id": "rm_test01",
            "topic": "test_topic",
            "status": "IN_PROGRESS",
            "tasks": tasks,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z"
        }
        exec_dir = tmp_path / ".build" / "execution" / "test_topic"
        exec_dir.mkdir(parents=True)
        state_file = exec_dir / "current.json"
        state_file.write_text(json.dumps(state), encoding="utf-8")
        return tmp_path

    def test_completed_tasks_are_skipped(self, tmp_path):
        from ape.intelligence.execution.engine import ExecutionEngine
        project_root = self._make_execution_state(
            tmp_path, {"tsk_1": "COMPLETED", "tsk_2": "PENDING"}
        )
        engine = ExecutionEngine(project_root, dry_run=True)
        summary = engine.resume_or_start("test_topic")
        # COMPLETED should not appear in executed tasks
        assert "tsk_1" not in summary["executed"]

    def test_failed_tasks_are_retried(self, tmp_path):
        from ape.intelligence.execution.engine import ExecutionEngine
        project_root = self._make_execution_state(
            tmp_path, {"tsk_1": "FAILED", "tsk_2": "PENDING"}
        )
        engine = ExecutionEngine(project_root, dry_run=True)
        summary = engine.resume_or_start("test_topic")
        assert "tsk_1" in summary["retried"]

    def test_pending_tasks_are_started(self, tmp_path):
        from ape.intelligence.execution.engine import ExecutionEngine
        project_root = self._make_execution_state(
            tmp_path, {"tsk_1": "PENDING"}
        )
        engine = ExecutionEngine(project_root, dry_run=True)
        summary = engine.resume_or_start("test_topic")
        assert "tsk_1" in summary["executed"]


# ---------------------------------------------------------------------------
# Ctrl+C simulation
# ---------------------------------------------------------------------------

class TestCtrlCPause:
    def test_keyboard_interrupt_produces_paused_state(self, tmp_path):
        from ape.intelligence.execution.engine import ExecutionEngine
        # Setup minimal roadmap
        roadmap_dir = tmp_path / ".build" / "roadmaps"
        roadmap_dir.mkdir(parents=True)
        roadmap = {
            "roadmap_id": "rm_test01",
            "decision_id": "dec_test",
            "goal": "Test",
            "milestones": [{
                "milestone_id": "ms_1",
                "title": "Test Milestone",
                "tasks": [
                    {
                        "task_id": "tsk_1_1",
                        "description": "Test task",
                        "deliverables": [],
                        "estimated_effort": "1h"
                    }
                ],
                "dependencies": []
            }],
            "estimated_time": "1h",
            "risks": [],
            "metadata": {},
            "timestamp": "2026-01-01T00:00:00Z"
        }
        (roadmap_dir / "test_topic.json").write_text(
            json.dumps(roadmap), encoding="utf-8"
        )

        # Use interrupt_after to simulate KeyboardInterrupt after first task
        # RFC-014: execute() now requires a decision artifact to exist.
        decision_file = tmp_path / ".build" / "decisions" / "test_topic.json"
        decision_file.parent.mkdir(parents=True, exist_ok=True)
        decision_file.write_text(json.dumps({"decision": "BUILD"}))

        engine = ExecutionEngine(
            tmp_path, dry_run=True, interrupt_after_tasks=1
        )
        engine.execute("test_topic", "test_topic")

        state_file = tmp_path / ".build" / "execution" / "test_topic" / "current.json"
        assert state_file.exists()
        state = json.loads(state_file.read_text())
        assert state["status"] == "PAUSED"

        from ape.utils import get_artifact_history
        evidence = get_artifact_history(tmp_path / ".governance" / "evidence", "execution")
        assert evidence.exists()
        events = [json.loads(line) for line in evidence.read_text().splitlines() if line]
        event_types = [e.get("event") for e in events]
        assert "PAUSED" in event_types


# ---------------------------------------------------------------------------
# Evidence JSONL events
# ---------------------------------------------------------------------------

class TestEvidenceLog:
    def test_evidence_records_completed_event(self, tmp_path):
        from ape.intelligence.execution.engine import ExecutionEngine
        roadmap_dir = tmp_path / ".build" / "roadmaps"
        roadmap_dir.mkdir(parents=True)
        roadmap = {
            "roadmap_id": "rm_ev01",
            "decision_id": "dec_ev",
            "goal": "Test",
            "milestones": [{
                "milestone_id": "ms_1",
                "title": "Evidence Test",
                "tasks": [{
                    "task_id": "tsk_ev_1",
                    "description": "evidence task",
                    "deliverables": [],
                    "estimated_effort": "1h"
                }],
                "dependencies": []
            }],
            "estimated_time": "1h",
            "risks": [],
            "metadata": {},
            "timestamp": "2026-01-01T00:00:00Z"
        }
        (roadmap_dir / "ev_topic.json").write_text(
            json.dumps(roadmap), encoding="utf-8"
        )

        engine = ExecutionEngine(tmp_path, dry_run=True)
        # RFC-014: execute() requires a decision artifact
        decision_file = tmp_path / ".build" / "decisions" / "ev_topic.json"
        decision_file.parent.mkdir(parents=True, exist_ok=True)
        decision_file.write_text(json.dumps({"decision": "BUILD"}))
        
        engine.execute("Evidence Topic", "ev_topic")

        from ape.utils import get_artifact_history
        evidence = get_artifact_history(tmp_path / ".governance" / "evidence", "execution")
        assert evidence.exists()
        events = [json.loads(line) for line in evidence.read_text().splitlines() if line]
        event_types = {e.get("event") for e in events}
        assert "STARTED" in event_types
        assert "COMPLETED" in event_types


# ---------------------------------------------------------------------------
# Dry-run guarantee
# ---------------------------------------------------------------------------

class TestDryRun:
    def test_dry_run_creates_no_real_files_outside_state(self, tmp_path):
        from ape.intelligence.execution.engine import ExecutionEngine
        roadmap_dir = tmp_path / ".build" / "roadmaps"
        roadmap_dir.mkdir(parents=True)
        roadmap = {
            "roadmap_id": "rm_dry",
            "decision_id": "dec_dry",
            "goal": "Dry Run Test",
            "milestones": [{
                "milestone_id": "ms_1",
                "title": "Build",
                "tasks": [{
                    "task_id": "tsk_dry_1",
                    "description": "create important_file.py",
                    "deliverables": ["important_file.py"],
                    "estimated_effort": "1h"
                }],
                "dependencies": []
            }],
            "estimated_time": "1h",
            "risks": [],
            "metadata": {},
            "timestamp": "2026-01-01T00:00:00Z"
        }
        (roadmap_dir / "dry_topic.json").write_text(
            json.dumps(roadmap), encoding="utf-8"
        )

        engine = ExecutionEngine(tmp_path, dry_run=True)
        # RFC-014: execute() requires a decision artifact
        decision_file = tmp_path / ".build" / "decisions" / "dry_topic.json"
        decision_file.parent.mkdir(parents=True, exist_ok=True)
        decision_file.write_text(json.dumps({"decision": "BUILD"}))
        
        engine.execute("Dry Topic", "dry_topic")

        # The deliverable must NOT actually be created in dry-run
        assert not (tmp_path / "important_file.py").exists()

    def test_dry_run_does_not_pollute_execution_state(self, tmp_path):
        """dry-run should not overwrite an existing real execution state."""
        from ape.intelligence.execution.engine import ExecutionEngine
        # Pre-create a real state
        exec_dir = tmp_path / ".build" / "execution" / "dry_topic"
        exec_dir.mkdir(parents=True)
        real_state = {"status": "COMPLETED", "sentinel": "real"}
        (exec_dir / "current.json").write_text(
            json.dumps(real_state), encoding="utf-8"
        )

        roadmap_dir = tmp_path / ".build" / "roadmaps"
        roadmap_dir.mkdir(parents=True)
        roadmap = {
            "roadmap_id": "rm_dry2",
            "decision_id": "dec_dry2",
            "goal": "Dry",
            "milestones": [],
            "estimated_time": "1h",
            "risks": [],
            "metadata": {},
            "timestamp": "2026-01-01T00:00:00Z"
        }
        (roadmap_dir / "dry_topic.json").write_text(
            json.dumps(roadmap), encoding="utf-8"
        )

        engine = ExecutionEngine(tmp_path, dry_run=True)
        # RFC-014: execute() requires a decision artifact
        decision_file = tmp_path / ".build" / "decisions" / "dry_topic.json"
        decision_file.parent.mkdir(parents=True, exist_ok=True)
        decision_file.write_text(json.dumps({"decision": "BUILD"}))
        
        engine.execute("Dry Topic", "dry_topic")

        state = json.loads((exec_dir / "current.json").read_text())
        assert state.get("sentinel") == "real"


# ---------------------------------------------------------------------------
# Approval gate
# ---------------------------------------------------------------------------

class TestApprovalGate:
    def test_modify_file_task_enters_requires_approval_before_execute(self, tmp_path):
        from ape.intelligence.execution.engine import ExecutionEngine
        roadmap_dir = tmp_path / ".build" / "roadmaps"
        roadmap_dir.mkdir(parents=True)
        roadmap = {
            "roadmap_id": "rm_appr",
            "decision_id": "dec_appr",
            "goal": "Approval Test",
            "milestones": [{
                "milestone_id": "ms_1",
                "title": "Modify Something",
                "tasks": [{
                    "task_id": "tsk_appr_1",
                    "description": "modify existing config.yaml",
                    "action": "modify_file",
                    "deliverables": [],
                    "estimated_effort": "1h"
                }],
                "dependencies": []
            }],
            "estimated_time": "1h",
            "risks": [],
            "metadata": {},
            "timestamp": "2026-01-01T00:00:00Z"
        }
        (roadmap_dir / "appr_topic.json").write_text(
            json.dumps(roadmap), encoding="utf-8"
        )

        # Execute with auto_deny to simulate user saying N
        engine = ExecutionEngine(tmp_path, dry_run=True, auto_deny_approvals=True)
        # RFC-014: execute() requires a decision artifact
        decision_file = tmp_path / ".build" / "decisions" / "appr_topic.json"
        decision_file.parent.mkdir(parents=True, exist_ok=True)
        decision_file.write_text(json.dumps({"decision": "BUILD"}))
        
        engine.execute("Approval Topic", "appr_topic")

        state_file = (
            tmp_path / ".build" / "execution" / "appr_topic" / "current.json"
        )
        state = json.loads(state_file.read_text())
        task_statuses = {t["task_id"]: t["status"] for t in state["tasks"]}
        assert task_statuses["tsk_appr_1"] == "REQUIRES_APPROVAL"
