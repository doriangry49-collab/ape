
from typer.testing import CliRunner

from ape.cli import app

runner = CliRunner()

def test_version_command_prints_package_version() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.output.strip() == "0.1.0"

def test_existing_cli_commands_still_succeed_with_project_config(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PWD", raising=False)
    (tmp_path / ".ape").mkdir()
    (tmp_path / ".ape" / "config.toml").write_text("[ape]\n", encoding="utf-8")

    version_result = runner.invoke(app, ["version"])
    config_result = runner.invoke(app, ["config"])
    doctor_result = runner.invoke(app, ["doctor"])

    assert version_result.exit_code == 0
    assert config_result.exit_code == 0
    assert doctor_result.exit_code == 0

def test_init_command_creates_ape_directory_and_config(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PWD", raising=False)

    first_result = runner.invoke(app, ["init"])
    second_result = runner.invoke(app, ["init"])

    assert first_result.exit_code == 0
    assert second_result.exit_code == 0
    assert ".ape/" in first_result.output
    assert "config.toml" in first_result.output
    assert (tmp_path / ".ape").is_dir()
    assert (tmp_path / ".ape" / "config.toml").is_file()

def test_init_command_uses_cwd_for_target_directory(tmp_path, monkeypatch) -> None:
    """init uses Path.cwd() (cross-platform); PWD env var is intentionally ignored."""
    target_dir = tmp_path / "target"
    target_dir.mkdir()

    monkeypatch.chdir(target_dir)

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert (target_dir / ".ape").is_dir()
    assert (target_dir / ".ape" / "config.toml").is_file()

def test_config_command_reports_workspace_status_from_current_directory(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PWD", raising=False)

    init_result = runner.invoke(app, ["init"])
    config_result = runner.invoke(app, ["config"])

    assert init_result.exit_code == 0
    assert config_result.exit_code == 0
    assert f"Workspace: {tmp_path}" in config_result.output
    assert f"Config: {tmp_path / '.ape' / 'config.toml'}" in config_result.output
    assert "Status: OK" in config_result.output

def test_config_command_reports_workspace_status_from_parent_directory(
    tmp_path, monkeypatch
) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / ".ape").mkdir()
    (workspace_dir / ".ape" / "config.toml").write_text("[ape]\n", encoding="utf-8")

    child_dir = workspace_dir / "child"
    child_dir.mkdir()

    monkeypatch.chdir(child_dir)
    monkeypatch.delenv("PWD", raising=False)

    result = runner.invoke(app, ["config"])

    assert result.exit_code == 0
    assert f"Workspace: {workspace_dir}" in result.output
    assert f"Config: {workspace_dir / '.ape' / 'config.toml'}" in result.output
    assert "Status: OK" in result.output

def test_config_command_errors_without_workspace(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PWD", raising=False)

    result = runner.invoke(app, ["config"])

    assert result.exit_code == 1
    assert "Error: no APE workspace found" in result.output


def test_cli_release_missing_execution_state_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".ape").mkdir()
    (tmp_path / ".ape" / "config.toml").write_text("[ape]\n", encoding="utf-8")

    result = runner.invoke(app, ["release", "nonexistent_topic"])

    assert result.exit_code == 1
    assert "Release Error:" in result.output


def test_cli_release_with_auto_approve(tmp_path, monkeypatch) -> None:
    import json
    import subprocess

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".ape").mkdir()
    (tmp_path / ".ape" / "config.toml").write_text("[ape]\n", encoding="utf-8")

    # Init git repo
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "APE Agent"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "agent@ape.dev"], cwd=tmp_path, check=True)
    (tmp_path / "init.txt").write_text("init")
    subprocess.run(["git", "add", "init.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True)

    # Create state
    state_dir = tmp_path / ".build" / "execution" / "test_calc"
    state_dir.mkdir(parents=True)
    state = {
        "execution_id": "exec_cli_01",
        "roadmap_id": "rm_cli_01",
        "topic": "test_calc",
        "decision_id": "dec_cli_01",
        "policy_decision": "BUILD",
        "evidence_hash": "hash_cli_01",
        "status": "COMPLETED",
        "tasks": []
    }
    (state_dir / "current.json").write_text(json.dumps(state))
    (tmp_path / "calc.py").write_text("def add(a, b): return a + b\n")

    result = runner.invoke(app, ["release", "test_calc", "--yes"])

    assert result.exit_code == 0
    assert "Successfully staged and committed release." in result.output
    assert "dec_cli_01" in result.output


def test_cli_release_user_prompt_declined(tmp_path, monkeypatch) -> None:
    import json
    import subprocess

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".ape").mkdir()
    (tmp_path / ".ape" / "config.toml").write_text("[ape]\n", encoding="utf-8")

    # Init git repo
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "APE Agent"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "agent@ape.dev"], cwd=tmp_path, check=True)
    (tmp_path / "init.txt").write_text("init")
    subprocess.run(["git", "add", "init.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True)

    # Create state
    state_dir = tmp_path / ".build" / "execution" / "test_calc"
    state_dir.mkdir(parents=True)
    state = {
        "execution_id": "exec_cli_02",
        "roadmap_id": "rm_cli_02",
        "topic": "test_calc",
        "decision_id": "dec_cli_02",
        "policy_decision": "BUILD",
        "evidence_hash": "hash_cli_02",
        "status": "COMPLETED",
        "tasks": []
    }
    (state_dir / "current.json").write_text(json.dumps(state))
    (tmp_path / "calc.py").write_text("def add(a, b): return a + b\n")

    # User inputs 'N'
    result = runner.invoke(app, ["release", "test_calc"], input="N\n")

    assert result.exit_code == 1
    assert "Release aborted or failed." in result.output

def test_doctor_command_succeeds_and_prints_status() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "APE Environment Status" in result.output
    assert "python" in result.output.lower()


def test_cli_does_not_use_project_load_directly() -> None:
    """CLI should use load_project factory instead of Project.load directly."""
    from pathlib import Path
    
    cli_path = Path(__file__).parent.parent / "src" / "ape" / "cli.py"
    cli_source = cli_path.read_text(encoding="utf-8")
    
    assert "Project.load(" not in cli_source, (
        "CLI must use load_project() factory, not Project.load() directly"
    )


