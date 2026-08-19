"""
Security Unit & Pipeline Tests for ExecutionAuthToken Boundary & Audit Trail — ORION-146 Phase A & C.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import pytest

from ape.intelligence.execution.agent import ApeCoderAgent
from ape.intelligence.execution.auth_token import (
    ExecutionAuthToken,
    get_governance_secret,
    create_test_auth_token,
)
from ape.intelligence.execution.engine import ExecutionEngine
from ape.intelligence.execution.executor import DockerSandboxExecutor, SandboxResult
from ape.intelligence.roadmap.llm import PlannerModel
from ape.pipeline.stages.policy_gate import PolicyGateStage


def test_execute_command_rejects_missing_token():
    """a) Rejects execution when auth_token is None; subprocess.run MUST NOT be called."""
    executor = DockerSandboxExecutor()
    with mock.patch("subprocess.run") as mock_run:
        result = executor.execute_command("echo unauthorized", auth_token=None)

        assert result.status == "BLOCKED"
        assert result.exit_code == -1
        assert "Unauthorized: valid ExecutionAuthToken required." in result.error
        assert mock_run.call_count == 0


def test_execute_command_rejects_forged_token():
    """b) Rejects execution when token signature is forged/invalid."""
    executor = DockerSandboxExecutor()
    forged_token = ExecutionAuthToken(
        task_id="task-forged",
        issued_at=datetime.now(timezone.utc).timestamp(),
        signature="invalid_signature_1234567890abcdef",
        issuer="PolicyGateStage",
    )

    with mock.patch("subprocess.run") as mock_run:
        result = executor.execute_command("echo forged", auth_token=forged_token)

        assert result.status == "BLOCKED"
        assert result.exit_code == -1
        assert "Unauthorized: valid ExecutionAuthToken required." in result.error
        assert mock_run.call_count == 0


def test_execute_command_rejects_expired_token():
    """c) Rejects execution when token freshness window (>300s) is exceeded."""
    executor = DockerSandboxExecutor()
    secret = get_governance_secret()
    # Issue token 301 seconds in the past
    expired_timestamp = datetime.now(timezone.utc).timestamp() - 301.0

    import hashlib
    import hmac
    msg = f"PolicyGateStage:task-expired:{expired_timestamp}".encode("utf-8")
    sig = hmac.new(secret, msg, hashlib.sha256).hexdigest()

    expired_token = ExecutionAuthToken(
        task_id="task-expired",
        issued_at=expired_timestamp,
        signature=sig,
        issuer="PolicyGateStage",
    )

    with mock.patch("subprocess.run") as mock_run:
        result = executor.execute_command("echo expired", auth_token=expired_token)

        assert result.status == "BLOCKED"
        assert result.exit_code == -1
        assert "Unauthorized: valid ExecutionAuthToken required." in result.error
        assert mock_run.call_count == 0


def test_execute_command_accepts_valid_policy_gate_token():
    """d) Proves execution accepts token issued by PolicyGateStage.issue_execution_token()."""
    executor = DockerSandboxExecutor()
    valid_token = PolicyGateStage.issue_execution_token("task-policy-approved")

    with (
        mock.patch("shutil.which", return_value="docker"),
        mock.patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Policy approved execution OK\n"
        mock_run.return_value.stderr = ""

        result = executor.execute_command("echo authorized", auth_token=valid_token)

        assert result.status == "COMPLETED"
        assert result.exit_code == 0
        assert "Policy approved execution OK" in result.output
        assert mock_run.call_count > 0


def test_production_missing_secret_fails_closed(monkeypatch):
    """e) Proves APE_ENV=production fails closed with RuntimeError if APE_GOVERNANCE_SECRET is missing."""
    monkeypatch.setenv("APE_ENV", "production")
    monkeypatch.delenv("APE_GOVERNANCE_SECRET", raising=False)

    with pytest.raises(RuntimeError, match="Production environment requires APE_GOVERNANCE_SECRET"):
        get_governance_secret()


# ---------------------------------------------------------------------------
# ORION-146 Phase C — Priority 1: Unauthorized Attempt Audit Trail Tests
# ---------------------------------------------------------------------------

def test_unauthorized_attempt_logged_to_evidence(tmp_path: Path):
    """Priority 1a: Verifies unauthorized attempt is logged to execution_unauthorized track when evidence_dir is set."""
    executor = DockerSandboxExecutor(evidence_dir=tmp_path)
    result = executor.execute_command("echo unauthorized_cmd", auth_token=None)

    assert result.status == "BLOCKED"
    log_files = list(tmp_path.glob("execution_unauthorized-*.jsonl"))
    assert len(log_files) == 1

    lines = [json.loads(line) for line in log_files[0].read_text(encoding="utf-8").strip().split("\n") if line.strip()]
    assert len(lines) == 1
    assert lines[0]["event"] == "UNAUTHORIZED_EXECUTION_ATTEMPT"
    assert lines[0]["reason"] == "Missing or invalid ExecutionAuthToken"
    assert lines[0]["cmd"] == "echo unauthorized_cmd"
    assert lines[0]["task_id"] == "UNKNOWN"


def test_unauthorized_attempt_without_evidence_dir_logs_warning(caplog):
    """Priority 1b: Verifies warning log is produced when evidence_dir is None (no silent drop)."""
    executor = DockerSandboxExecutor(evidence_dir=None)

    with caplog.at_level(logging.WARNING, logger="ape.security"):
        result = executor.execute_command("echo silent_test", auth_token=None)

    assert result.status == "BLOCKED"
    assert "Unauthorized execute_command() attempt rejected without evidence_dir configured" in caplog.text


# ---------------------------------------------------------------------------
# ORION-146 Phase C — Priority 2: Pipeline-Level E2E Rejection Test
# ---------------------------------------------------------------------------

class MockPlannerLLM(PlannerModel):
    def generate(self, prompt: str, system_message: str, schema: dict) -> dict:
        return {"thought": "Try execution", "action": "run_tests", "params": {}}


def test_pipeline_rejects_execution_with_invalid_token(tmp_path: Path, monkeypatch):
    """Priority 2 (Madde 6): Verifies full ExecutionEngine pipeline halts when PolicyGate issues an invalid/expired token."""
    project_root = tmp_path / "workspace"
    project_root.mkdir()

    decisions_dir = project_root / ".build" / "decisions"
    decisions_dir.mkdir(parents=True)
    (decisions_dir / "test_app.json").write_text(json.dumps({
        "decision_id": "dec_p2_01",
        "decision": "BUILD",
        "policy": "Core Policy",
        "evidence_hash": "hash_p2",
    }))

    roadmaps_dir = project_root / ".build" / "roadmaps"
    roadmaps_dir.mkdir(parents=True)
    (roadmaps_dir / "test_app.json").write_text(json.dumps({
        "roadmap_id": "rm_p2_01",
        "decision_id": "dec_p2_01",
        "policy_decision": "BUILD",
        "goal": "Build app",
        "milestones": [{
            "milestone_id": "ms_1",
            "title": "M1",
            "dependencies": [],
            "tasks": [{
                "task_id": "task_invalid_token",
                "description": "Task with invalid token",
                "action": "run_tests",
                "deliverables": [],
            }]
        }]
    }))

    # Monkeypatch PolicyGateStage to issue an expired token (issued 301 seconds ago)
    secret = get_governance_secret()
    expired_ts = datetime.now(timezone.utc).timestamp() - 301.0
    import hashlib
    import hmac
    msg = f"PolicyGateStage:task_invalid_token:{expired_ts}".encode("utf-8")
    sig = hmac.new(secret, msg, hashlib.sha256).hexdigest()
    invalid_token = ExecutionAuthToken(
        task_id="task_invalid_token",
        issued_at=expired_ts,
        signature=sig,
        issuer="PolicyGateStage",
    )

    monkeypatch.setattr(PolicyGateStage, "issue_execution_token", lambda task_id: invalid_token)

    executor = DockerSandboxExecutor(evidence_dir=project_root / ".governance" / "evidence")
    agent = ApeCoderAgent(model=MockPlannerLLM())
    engine = ExecutionEngine(project_root=project_root, dry_run=False, executor=executor, agent=agent)

    result = engine.execute("Test App", "test_app")
    assert "task_invalid_token" not in result.get("executed", [])

    # Check evidence log records the rejection
    evidence_dir = project_root / ".governance" / "evidence"
    agent_logs = list(evidence_dir.glob("execution_agent-*.jsonl"))
    assert len(agent_logs) > 0
    records = [json.loads(line) for line in agent_logs[0].read_text().strip().split("\n") if line.strip()]
    assert len(records) > 0
    assert "Unauthorized: valid ExecutionAuthToken required." in records[0]["stderr"]


# ---------------------------------------------------------------------------
# ORION-146 Phase C — Priority 3: Lineage Assertion Test
# ---------------------------------------------------------------------------

def test_auth_token_task_id_matches_evidence_record(tmp_path: Path):
    """Priority 3 (Madde 5): Asserts that task_id in ExecutionAuthToken matches task_id in disk evidence record."""
    project_root = tmp_path / "workspace"
    project_root.mkdir()

    decisions_dir = project_root / ".build" / "decisions"
    decisions_dir.mkdir(parents=True)
    (decisions_dir / "lineage_app.json").write_text(json.dumps({
        "decision_id": "dec_lineage_01",
        "decision": "BUILD",
        "policy": "Core Policy",
        "evidence_hash": "hash_lineage",
    }))

    roadmaps_dir = project_root / ".build" / "roadmaps"
    roadmaps_dir.mkdir(parents=True)
    target_task_id = "task_lineage_999"
    (roadmaps_dir / "lineage_app.json").write_text(json.dumps({
        "roadmap_id": "rm_lineage_01",
        "decision_id": "dec_lineage_01",
        "policy_decision": "BUILD",
        "goal": "Build lineage app",
        "milestones": [{
            "milestone_id": "ms_1",
            "title": "M1",
            "dependencies": [],
            "tasks": [{
                "task_id": target_task_id,
                "description": "Lineage assertion task",
                "action": "run_tests",
                "deliverables": [],
            }]
        }]
    }))

    issued_tokens: list[ExecutionAuthToken] = []
    original_issue_token = PolicyGateStage.issue_execution_token

    def spy_issue_token(task_id: str) -> ExecutionAuthToken:
        token = original_issue_token(task_id)
        issued_tokens.append(token)
        return token

    with (
        mock.patch.object(PolicyGateStage, "issue_execution_token", side_effect=spy_issue_token),
        mock.patch("shutil.which", return_value="docker"),
        mock.patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "OK"
        mock_run.return_value.stderr = ""

        executor = DockerSandboxExecutor(evidence_dir=project_root / ".governance" / "evidence")
        agent = ApeCoderAgent(model=MockPlannerLLM())
        engine = ExecutionEngine(project_root=project_root, dry_run=False, executor=executor, agent=agent)

        result = engine.execute("Lineage App", "lineage_app")
        assert target_task_id in result.get("executed", [])

    # Read disk JSONL evidence record from .governance/evidence/execution_agent-*.jsonl
    evidence_dir = project_root / ".governance" / "evidence"
    agent_log_files = list(evidence_dir.glob("execution_agent-*.jsonl"))
    assert len(agent_log_files) > 0

    records = [json.loads(line) for line in agent_log_files[0].read_text().strip().split("\n") if line.strip()]
    assert len(records) > 0
    disk_record_task_id = records[0]["task_id"]

    assert len(issued_tokens) > 0
    token_task_id = issued_tokens[0].task_id

    # CRITICAL LINEAGE ASSERTION: Token task_id MUST match disk evidence record task_id!
    assert token_task_id == target_task_id
    assert disk_record_task_id == target_task_id
    assert token_task_id == disk_record_task_id


# ---------------------------------------------------------------------------
# ORION-146 Phase C — Priority 4: Double-Fault Scenario Test
# ---------------------------------------------------------------------------

def test_double_fault_unauthorized_and_sanitizer_failure(tmp_path: Path, monkeypatch):
    """Priority 4 (Madde 7): Tests fail-closed behavior when an unauthorized attempt occurs AND sanitizer throws an exception."""
    executor = DockerSandboxExecutor(evidence_dir=tmp_path)

    def mock_broken_sanitizer(payload, max_depth=10):
        raise RuntimeError("Simulated Sanitizer Crash")

    monkeypatch.setattr("ape.utils.sanitize_evidence_payload", mock_broken_sanitizer)

    result = executor.execute_command("echo secret_key_test", auth_token=None)

    assert result.status == "BLOCKED"
    log_files = list(tmp_path.glob("execution_unauthorized-*.jsonl"))
    assert len(log_files) == 1

    records = [json.loads(line) for line in log_files[0].read_text().strip().split("\n") if line.strip()]
    assert len(records) == 1
    assert records[0]["event"] == "REDACTION_FAILURE"
    assert "Sanitizer failed to process payload safely" in records[0]["error"]
