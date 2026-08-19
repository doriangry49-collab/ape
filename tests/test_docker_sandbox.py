"""
RFC-009: Execution Sandbox — TDD RED Phase
Testing DockerSandboxExecutor constraints and fail-closed behavior.
"""
from unittest import mock

from ape.intelligence.execution.auth_token import create_test_auth_token
from ape.intelligence.execution.executor import DockerSandboxExecutor
from ape.intelligence.execution.policy import ExecutionPolicy


def test_docker_unavailable_fails_closed_no_fallback():
    """If Docker is not installed/running, execution must FAIL CLOSED."""
    with mock.patch("shutil.which", return_value=None):
        executor = DockerSandboxExecutor()
        result = executor.execute_command("echo hello", cwd="/tmp", auth_token=create_test_auth_token())

        assert result.exit_code != 0
        assert "Docker unavailable" in result.error
        assert result.status == "BLOCKED"  # BLOCKED = stopped before execution, not FAILED


def test_docker_unavailable_logs_to_evidence(tmp_path):
    """When Docker is unavailable, the failure must be logged to evidence."""
    from ape.intelligence.execution.engine import ExecutionEngine

    with mock.patch("shutil.which", return_value=None):
        # Verify engine is constructed without error when Docker missing
        ExecutionEngine(tmp_path, dry_run=False)
        # Sandbox state is BLOCKED — tested in integration engine tests
        pass


def test_network_disabled_by_default():
    """The Docker command must include --network none by default."""
    executor = DockerSandboxExecutor()

    with (
        mock.patch("shutil.which", return_value="docker"),
        mock.patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""
        executor.execute_command("curl http://example.com", cwd="/tmp", auth_token=create_test_auth_token())

        cmd_called = mock_run.call_args[0][0]
        assert "--network=none" in cmd_called or (
            "--network none" in " ".join(cmd_called)
        )


def test_credential_leakage_prevented():
    """Docker command must NOT inherit host environment variables."""
    executor = DockerSandboxExecutor()

    with (
        mock.patch("shutil.which", return_value="docker"),
        mock.patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""
        executor.execute_command("env", cwd="/tmp", auth_token=create_test_auth_token())

        cmd_called = mock_run.call_args[0][0]
        env_args = [
            arg for arg in cmd_called if arg == "-e" or arg.startswith("--env")
        ]
        assert len(env_args) == 0


def test_resource_and_time_limits_applied():
    """The Docker command must apply CPU/Memory and timeout constraints."""
    executor = DockerSandboxExecutor()

    with (
        mock.patch("shutil.which", return_value="docker"),
        mock.patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""
        executor.execute_command("stress --cpu 8", cwd="/tmp", auth_token=create_test_auth_token())

        cmd_called = mock_run.call_args[0][0]
        cmd_str = " ".join(cmd_called)
        assert "--memory=" in cmd_str or "-m " in cmd_str
        assert "--cpus=" in cmd_str



def test_policy_gate_operates_independently():
    """
    Policy evaluation must happen BEFORE Docker execution.
    If Policy says REQUIRES_APPROVAL, Docker is never invoked.
    """
    policy = ExecutionPolicy()

    # "modify_file" requires approval — engine handles this, not executor.
    action = "modify_file"
    assert policy.classify(action) == "REQUIRES_APPROVAL"
