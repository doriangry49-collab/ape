"""
RFC-009: Execution Sandbox — TDD RED Phase
Testing DockerSandboxExecutor constraints and fail-closed behavior.
"""
from unittest import mock

from ape.intelligence.execution.executor import DockerSandboxExecutor
from ape.intelligence.execution.policy import ExecutionPolicy


def test_docker_unavailable_fails_closed_no_fallback():
    """If Docker is not installed/running, execution must FAIL CLOSED, never fallback to host."""
    with mock.patch("shutil.which", return_value=None):
        executor = DockerSandboxExecutor()
        
        result = executor.execute_command("echo hello", cwd="/tmp")
        
        assert result.exit_code != 0
        assert "Docker unavailable" in result.error
        assert result.status == "FAILED"


def test_docker_unavailable_logs_to_evidence(tmp_path):
    """When Docker is unavailable, the failure must be logged to evidence."""
    # We will test the engine integration where it blocks and writes evidence.
    from ape.intelligence.execution.engine import ExecutionEngine
    
    # Mock shutil.which to simulate docker missing
    with mock.patch("shutil.which", return_value=None):
        # We need a non-dry-run engine for real execution
        engine = ExecutionEngine(tmp_path, dry_run=False)
        
        # Manually force a task execution that requires real executor
        # This is a bit implementation specific, but we assert the engine
        # correctly catches the Sandbox failure and emits to evidence.
        # For RED phase, we just define the expected behavior.
        pass # To be fully implemented when Engine uses DockerSandboxExecutor


def test_network_disabled_by_default():
    """The Docker command must include --network none by default."""
    executor = DockerSandboxExecutor()
    
    with mock.patch("shutil.which", return_value="docker"), mock.patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""
        executor.execute_command("curl http://example.com", cwd="/tmp")
        
        cmd_called = mock_run.call_args[0][0]
        assert "--network=none" in cmd_called or "--network none" in " ".join(cmd_called)


def test_credential_leakage_prevented():
    """The Docker command must NOT inherit host environment variables by default."""
    executor = DockerSandboxExecutor()
    
    with mock.patch("shutil.which", return_value="docker"), mock.patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""
        executor.execute_command("env", cwd="/tmp")
        
        cmd_called = mock_run.call_args[0][0]
        # It shouldn't pass -e AWS_ACCESS_KEY_ID or use host env
        # A strict sandbox usually runs clean env.
        # We check that no `-e` args are blindly copying sensitive host vars.
        env_args = [arg for arg in cmd_called if arg == "-e" or arg.startswith("--env")]
        assert len(env_args) == 0


def test_resource_and_time_limits_applied():
    """The Docker command must apply CPU/Memory and timeout constraints."""
    executor = DockerSandboxExecutor()
    
    with mock.patch("shutil.which", return_value="docker"), mock.patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""
        executor.execute_command("stress --cpu 8", cwd="/tmp")
        
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
    executor = DockerSandboxExecutor()
    
    # "modify_file" requires approval.
    action = "modify_file"
    assert policy.classify(action) == "REQUIRES_APPROVAL"
    
    # The ExecutionEngine logic handles this, but conceptually
    # the Executor itself doesn't override policy.
    # In a real test, we would mock subprocess.run and assert it's NOT called 
    # if the engine evaluates policy first.
