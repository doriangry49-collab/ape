from pathlib import Path

from typer.testing import CliRunner

from ape.cli import app

runner = CliRunner()


def test_version_command_prints_package_version() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.output.strip() == "0.1.0"


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


def test_init_command_uses_pwd_for_target_directory(tmp_path, monkeypatch) -> None:
    package_root = Path(__file__).resolve().parents[1]
    target_dir = tmp_path / "target"
    target_dir.mkdir()

    monkeypatch.chdir(package_root)
    monkeypatch.setenv("PWD", str(target_dir))

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert (target_dir / ".ape").is_dir()
    assert (target_dir / ".ape" / "config.toml").is_file()


def test_config_command_reports_workspace_status(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PWD", raising=False)

    init_result = runner.invoke(app, ["init"])
    config_result = runner.invoke(app, ["config"])

    assert init_result.exit_code == 0
    assert config_result.exit_code == 0
    assert f"Workspace: {tmp_path}" in config_result.output
    assert f"Config: {tmp_path / '.ape' / 'config.toml'}" in config_result.output
    assert "Status: OK" in config_result.output


def test_config_command_errors_without_workspace(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PWD", raising=False)

    result = runner.invoke(app, ["config"])

    assert result.exit_code == 1
    assert "Error: no APE workspace found" in result.output


def test_doctor_command_succeeds_and_prints_status() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "APE Environment Status" in result.output
    assert "python" in result.output.lower()
