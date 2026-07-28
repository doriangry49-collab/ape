"""
RFC-009/RFC-010: Docker Sandbox Integration Tests
These tests run REAL Docker commands. They are skipped locally if Docker is
unavailable and run unconditionally in CI (ubuntu-latest runner has Docker).
"""
import os
import shutil

import pytest

from ape.intelligence.execution.executor import DockerSandboxExecutor

DOCKER_AVAILABLE = shutil.which("docker") is not None


@pytest.mark.integration
@pytest.mark.skipif(
    not DOCKER_AVAILABLE, reason="Docker is not installed or available on PATH"
)
class TestDockerIntegration:

    def test_real_docker_execution(self):
        """A simple command should execute inside the container."""
        executor = DockerSandboxExecutor()
        result = executor.execute_command("echo hello world", cwd="/tmp")

        assert result.exit_code == 0
        assert result.status == "COMPLETED"
        assert "hello world" in result.output

    def test_environment_isolation(self):
        """Host environment variables must NOT leak into the sandbox."""
        os.environ["SECRET_TEST_VAR"] = "SUPER_SECRET"
        try:
            executor = DockerSandboxExecutor()
            result = executor.execute_command("env", cwd="/tmp")

            assert result.exit_code == 0
            assert "SECRET_TEST_VAR" not in result.output
            assert "SUPER_SECRET" not in result.output
        finally:
            del os.environ["SECRET_TEST_VAR"]

    def test_network_isolation(self):
        """The container must not have external network access."""
        executor = DockerSandboxExecutor()
        result = executor.execute_command("ping -c 1 1.1.1.1", cwd="/tmp")

        assert result.exit_code != 0
        assert result.status == "FAILED"
        assert (
            "unreachable" in result.error.lower()
            or "unreachable" in result.output.lower()
            or "network is down" in result.error.lower()
        )

    def test_timeout_constraint(self):
        """Execution must be terminated and return FAILED when timeout is exceeded."""
        executor = DockerSandboxExecutor()
        # Use the real timeout parameter: 1 second, container sleeps 5
        result = executor.execute_command("sleep 5", cwd="/tmp", timeout=1)

        assert result.exit_code == -1
        assert result.status == "FAILED"
        assert "timed out" in result.error

    def test_exit_code_propagation(self):
        """Container exit code must propagate faithfully through SandboxResult."""
        executor = DockerSandboxExecutor()
        # sh -c "exit 42" produces exit code 42
        result = executor.execute_command("exit 42", cwd="/tmp")

        assert result.exit_code == 42
        assert result.status == "FAILED"
