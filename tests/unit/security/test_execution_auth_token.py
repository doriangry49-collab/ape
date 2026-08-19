"""
Security Unit Tests for ExecutionAuthToken Boundary — ORION-146 Phase A.
"""

import os
import time
from datetime import datetime, timezone
from unittest import mock

import pytest

from ape.intelligence.execution.auth_token import (
    ExecutionAuthToken,
    get_governance_secret,
    create_test_auth_token,
)
from ape.intelligence.execution.executor import DockerSandboxExecutor
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
