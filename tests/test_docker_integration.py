"""
RFC-009/RFC-010: Docker Sandbox Integration Tests
These tests run REAL Docker commands. They are skipped locally if Docker is
unavailable and run unconditionally in CI (ubuntu-latest runner has Docker).
"""
import os
import shutil
import subprocess

import pytest

from ape.intelligence.execution.auth_token import create_test_auth_token
from ape.intelligence.execution.executor import DockerSandboxExecutor


def _is_docker_daemon_active() -> bool:
    return DockerSandboxExecutor.get_docker_prefix() is not None


DOCKER_AVAILABLE = _is_docker_daemon_active()


@pytest.mark.integration
@pytest.mark.skipif(
    not DOCKER_AVAILABLE, reason="Docker daemon is not running or available on host"
)
class TestDockerIntegration:

    def test_real_docker_execution(self):
        """A simple command should execute inside the container."""
        executor = DockerSandboxExecutor()
        result = executor.execute_command("echo hello world", cwd="/tmp", auth_token=create_test_auth_token())

        assert result.exit_code == 0
        assert result.status == "COMPLETED"
        assert "hello world" in result.output

    def test_environment_isolation(self):
        """Host environment variables must NOT leak into the sandbox."""
        os.environ["SECRET_TEST_VAR"] = "SUPER_SECRET"
        try:
            executor = DockerSandboxExecutor()
            result = executor.execute_command("env", cwd="/tmp", auth_token=create_test_auth_token())

            assert result.exit_code == 0
            assert "SECRET_TEST_VAR" not in result.output
            assert "SUPER_SECRET" not in result.output
        finally:
            del os.environ["SECRET_TEST_VAR"]

    def test_network_isolation(self):
        executor = DockerSandboxExecutor()
        result = executor.execute_command(
            "wget -q --timeout=3 -O /dev/null http://1.1.1.1",
            cwd="/tmp",
            auth_token=create_test_auth_token(),
        )

        # wget must fail (network blocked)
        assert result.exit_code != 0, "Expected wget to fail with network unreachable"
        assert result.status == "FAILED"

        # Failure must be network-related, NOT a missing binary
        combined = (result.error + result.output).lower()
        assert "not found" not in combined, (
            "wget binary appears to be missing in Alpine — "
            "test is vacuous and does not prove network isolation."
        )
        assert (
            "unreachable" in combined
            or "network" in combined
            or "connect" in combined
        ), (
            f"Expected network-related error. Got stderr={result.error!r} "
            f"stdout={result.output!r}"
        )

    def test_timeout_constraint(self):
        """Execution must be terminated and return FAILED when timeout is exceeded."""
        executor = DockerSandboxExecutor()
        # Real Docker container sleeps 5 seconds; Python timeout is 1 second
        result = executor.execute_command("sleep 5", cwd="/tmp", timeout=1, auth_token=create_test_auth_token())

        assert result.exit_code == -1
        assert result.status == "FAILED"
        assert "timed out" in result.error

    def test_exit_code_propagation(self):
        """Container exit code must propagate faithfully through SandboxResult."""
        executor = DockerSandboxExecutor()
        result = executor.execute_command("exit 42", cwd="/tmp", auth_token=create_test_auth_token())

        assert result.exit_code == 42
        assert result.status == "FAILED"


# ---------------------------------------------------------------------------
# Daemon-independent tests: run unconditionally regardless of Docker availability
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_blocked_status_when_docker_unavailable(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    executor = DockerSandboxExecutor()
    result = executor.execute_command("echo test", cwd="/tmp", auth_token=create_test_auth_token())

    assert result.status == "BLOCKED"
    assert "Docker unavailable" in result.error
    assert result.exit_code == -1
