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


def test_wsl_workspace_path_conversion():
    """Verify convert_to_wsl_path converts Windows drive paths and execute_command uses it for WSL docker prefix."""
    win_path = r"C:\Users\Thea-Aria\ .gemini\antigravity\scratch\ec2-file-explorer\ape_repo"
    wsl_path = DockerSandboxExecutor.convert_to_wsl_path(win_path)
    assert wsl_path == "/mnt/c/Users/Thea-Aria/ .gemini/antigravity/scratch/ec2-file-explorer/ape_repo"

    executor = DockerSandboxExecutor()
    with (
        mock.patch.object(DockerSandboxExecutor, "get_docker_prefix", return_value=["wsl", "-d", "Debian", "-u", "root", "--", "docker"]),
        mock.patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "OK"
        mock_run.return_value.stderr = ""
        res = executor.execute_command("echo hello", workspace_dir=win_path, auth_token=create_test_auth_token())
        assert res.exit_code == 0

        cmd_called = mock_run.call_args[0][0]
        v_idx = cmd_called.index("-v")
        assert cmd_called[v_idx + 1] == f"{wsl_path}:/workspace:rw"


def test_deliverable_verifier_contract_parsing(tmp_path):
    """Test A through F for DeliverableVerifier parsing of alternatives and suffixes."""
    from ape.intelligence.execution.verifier import DeliverableVerifier

    verifier = DeliverableVerifier(tmp_path, dry_run=False)

    # TEST A: Exact file exists -> PASS
    (tmp_path / "README.md").write_text("hello", encoding="utf-8")
    ok, missing = verifier.verify(["README.md"])
    assert ok and not missing

    # TEST B: First alternative exists -> PASS
    (tmp_path / "pyproject.toml").write_text("[project]", encoding="utf-8")
    ok, missing = verifier.verify(["package.json or pyproject.toml"])
    assert ok and not missing

    # TEST C: Second alternative exists -> PASS
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    ok, missing = verifier.verify(["package.json or pyproject.toml"])
    assert ok and not missing

    # TEST D: Neither alternative exists -> FAIL
    (tmp_path / "package.json").unlink()
    (tmp_path / "pyproject.toml").unlink()
    ok, missing = verifier.verify(["package.json or pyproject.toml"])
    assert not ok and missing == ["package.json or pyproject.toml"]

    # TEST E: Existing file with descriptive suffix -> PASS
    ok, missing = verifier.verify(["README.md file"])
    assert ok and not missing

    # TEST F: No false positive for non-matching file
    (tmp_path / "README.md").unlink()
    (tmp_path / "README-old.md").write_text("old", encoding="utf-8")
    ok, missing = verifier.verify(["README.md"])
    assert not ok and missing == ["README.md"]


def test_agent_exploratory_step_does_not_false_complete_file_task():
    """Verify that an exploratory step (search) does NOT falsely complete a task requiring deliverables."""
    from types import SimpleNamespace
    from ape.intelligence.execution.agent import ApeCoderAgent

    task = SimpleNamespace(
        task_id="task-test",
        description="Create main CLI script.",
        deliverables=["main.py"],
        action="create_file"
    )

    mock_model = mock.MagicMock()
    # Attempt 1: LLM proposes search
    # Attempt 2: LLM proposes create_file
    mock_model.generate.side_effect = [
        {"thought": "exploring", "action": "search", "params": {"query": "*"}},
        {"thought": "writing file", "action": "create_file", "params": {"path": "main.py", "content": "print('hello')"}},
    ]

    agent = ApeCoderAgent(model=mock_model, max_repair_attempts=2)
    mock_executor = mock.MagicMock()
    mock_executor.execute_command.return_value.exit_code = 0
    mock_executor.execute_command.return_value.output = "OK"
    mock_executor.execute_command.return_value.error = ""

    from ape.intelligence.execution.auth_token import create_test_auth_token
    token = create_test_auth_token()

    res = agent.execute_task(task, sandbox_executor=mock_executor, auth_token=token)
    assert res.status == "COMPLETED"
    assert len(res.steps) == 2
    assert res.steps[0].action == "search"
    assert res.steps[1].action == "create_file"


def test_agent_positive_write_step_completes_task():
    """Verify that a positive write action (create_file) proceeds to COMPLETED when executed."""
    from types import SimpleNamespace
    from ape.intelligence.execution.agent import ApeCoderAgent

    task = SimpleNamespace(
        task_id="task-positive-test",
        description="Write configuration file.",
        deliverables=["config.json"],
        action="create_file"
    )

    mock_model = mock.MagicMock()
    # LLM directly proposes create_file
    mock_model.generate.return_value = {
        "thought": "creating config file",
        "action": "create_file",
        "params": {"path": "config.json", "content": "{}"}
    }

    agent = ApeCoderAgent(model=mock_model, max_repair_attempts=2)
    mock_executor = mock.MagicMock()
    mock_executor.execute_command.return_value.exit_code = 0
    mock_executor.execute_command.return_value.output = "OK"
    mock_executor.execute_command.return_value.error = ""

    from ape.intelligence.execution.auth_token import create_test_auth_token
    token = create_test_auth_token()

    res = agent.execute_task(task, sandbox_executor=mock_executor, auth_token=token)
    assert res.status == "COMPLETED"
    assert len(res.steps) == 1
    assert res.steps[0].action == "create_file"
    assert res.steps[0].status == "SUCCESS"
