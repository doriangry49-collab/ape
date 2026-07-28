"""
RFC-009: Docker Sandbox Integration Tests
These tests run REAL Docker commands if Docker is available.
If Docker is missing, they are skipped.
"""
import os
import shutil
import pytest
from ape.intelligence.execution.executor import DockerSandboxExecutor

DOCKER_AVAILABLE = shutil.which("docker") is not None

@pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker is not installed or available on PATH")
class TestDockerIntegration:
    
    def test_real_docker_execution(self):
        """A simple command should execute inside the container."""
        executor = DockerSandboxExecutor()
        # Alpine has 'echo'
        result = executor.execute_command("echo hello world", cwd="/tmp")
        
        assert result.exit_code == 0
        assert result.status == "COMPLETED"
        assert "hello world" in result.output

    def test_environment_isolation(self):
        """Host environment variables should NOT leak into the sandbox."""
        # Set a host env variable
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
        """The container should not have external network access."""
        executor = DockerSandboxExecutor()
        
        # Ping a known external IP (Cloudflare DNS)
        # It should fail because --network=none
        result = executor.execute_command("ping -c 1 1.1.1.1", cwd="/tmp")
        
        assert result.exit_code != 0
        assert result.status == "FAILED"
        # ping network unreachable message
        assert "unreachable" in result.error.lower() or "unreachable" in result.output.lower() or "network is down" in result.error.lower()

    def test_timeout_constraint(self):
        """The container should enforce the execution timeout."""
        executor = DockerSandboxExecutor()
        
        # We temporarily reduce the timeout just for this test by monkeypatching the run command, 
        # but to keep it fully real, we can just let it run for the full 60 seconds if we must, 
        # or we can pass a custom timeout flag to our execute_command if it existed.
        # Since execute_command has hardcoded 60s, this test would take 60s.
        # For CI speed, we'll patch the timeout parameter of subprocess.run just for this test
        # to ensure the timeout path works correctly.
        import subprocess
        from unittest import mock
        
        original_run = subprocess.run
        
        def run_with_short_timeout(*args, **kwargs):
            kwargs["timeout"] = 1  # 1 second timeout
            return original_run(*args, **kwargs)
            
        with mock.patch("subprocess.run", side_effect=run_with_short_timeout):
            # Sleep for 3 seconds, which will exceed our 1 second timeout
            result = executor.execute_command("sleep 3", cwd="/tmp")
            
            assert result.exit_code == -1
            assert result.status == "FAILED"
            assert "timed out" in result.error
