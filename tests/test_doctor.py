from pathlib import Path

import pytest
from typer.testing import CliRunner

from ape.cli import app
from ape.project import Project
from ape.services import (
    ConfigService,
    ProjectInfoService,
    ProjectValidationService,
    WorkspaceService,
)
from ape.workspace import find_workspace_dir

runner = CliRunner()


def test_version_command_prints_package_version() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.output.strip() == "0.1.0"


def test_find_workspace_dir_discovers_workspace_from_child_directory(tmp_path) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / ".ape").mkdir()
    (workspace_dir / ".ape" / "config.toml").write_text("[ape]\n", encoding="utf-8")

    child_dir = workspace_dir / "child"
    child_dir.mkdir()

    assert find_workspace_dir(child_dir) == workspace_dir


def test_project_load_discovers_workspace_from_parent_directory(tmp_path) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / ".ape").mkdir()
    (workspace_dir / ".ape" / "config.toml").write_text("[ape]\n", encoding="utf-8")

    child_dir = workspace_dir / "child"
    child_dir.mkdir()

    project = Project.load(child_dir)

    assert project.root == workspace_dir
    assert project.config_path == workspace_dir / ".ape" / "config.toml"
    assert project.exists() is True


def test_project_load_uses_path_when_workspace_is_missing(tmp_path) -> None:
    project = Project.load(tmp_path)

    assert project.root == tmp_path
    assert project.config_path == tmp_path / ".ape" / "config.toml"
    assert project.exists() is False


def test_project_config_parses_existing_workspace_config(tmp_path) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / ".ape").mkdir()
    (workspace_dir / ".ape" / "config.toml").write_text(
        '[ape]\nname = "demo"\n', encoding="utf-8"
    )

    project = Project.load(workspace_dir)

    assert project.config == {"ape": {"name": "demo"}}


def test_project_config_is_empty_when_config_file_is_missing(tmp_path) -> None:
    project = Project.load(tmp_path)

    assert project.exists() is False
    assert project.config == {}


def test_project_name_returns_config_value_when_available(tmp_path) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / ".ape").mkdir()
    (workspace_dir / ".ape" / "config.toml").write_text(
        '[ape]\nname = "demo"\n', encoding="utf-8"
    )

    project = Project.load(workspace_dir)

    assert project.name == "demo"


def test_project_name_returns_none_when_missing(tmp_path) -> None:
    project = Project.load(tmp_path)

    assert project.name is None


def test_project_info_returns_read_only_project_information(tmp_path) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / ".ape").mkdir()
    (workspace_dir / ".ape" / "config.toml").write_text(
        '[ape]\nname = "demo"\n', encoding="utf-8"
    )

    project = Project.load(workspace_dir)

    assert project.info["root"] == workspace_dir
    assert project.info["config_path"] == workspace_dir / ".ape" / "config.toml"
    assert project.info["exists"] is True
    assert project.info["name"] == "demo"

    with pytest.raises(TypeError):
        project.info["name"] = "other"


def test_project_metadata_contains_project_state(tmp_path) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / ".ape").mkdir()
    (workspace_dir / ".ape" / "config.toml").write_text(
        '[ape]\nname = "demo"\n', encoding="utf-8"
    )

    project = Project.load(workspace_dir)

    assert project.metadata == {
        "root": workspace_dir,
        "config_path": workspace_dir / ".ape" / "config.toml",
        "exists": True,
        "name": "demo",
    }


def test_config_service_exposes_read_only_project_configuration(tmp_path) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / ".ape").mkdir()
    (workspace_dir / ".ape" / "config.toml").write_text(
        '[ape]\nname = "demo"\n', encoding="utf-8"
    )

    project = Project.load(workspace_dir)
    service = ConfigService(project)

    assert service.project_name == "demo"
    assert service.config_exists is True
    assert service.config == {"ape": {"name": "demo"}}
    assert service.config_path == workspace_dir / ".ape" / "config.toml"


def test_config_service_handles_missing_config(tmp_path) -> None:
    project = Project.load(tmp_path)
    service = ConfigService(project)

    assert service.project_name is None
    assert service.config_exists is False
    assert service.config == {}
    assert service.config_path == tmp_path / ".ape" / "config.toml"


def test_project_info_service_exposes_read_only_project_information(tmp_path) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / ".ape").mkdir()
    (workspace_dir / ".ape" / "config.toml").write_text(
        '[ape]\nname = "demo"\n', encoding="utf-8"
    )

    project = Project.load(workspace_dir)
    service = ProjectInfoService(project)

    assert service.root == workspace_dir
    assert service.config_path == workspace_dir / ".ape" / "config.toml"
    assert service.exists is True
    assert service.name == "demo"
    assert service.info == project.info
    assert service.metadata == project.metadata
    assert service.config == project.config

    with pytest.raises(TypeError):
        service.info["name"] = "other"


def test_workspace_service_discovers_workspace_from_child_directory(tmp_path) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / ".ape").mkdir()
    (workspace_dir / ".ape" / "config.toml").write_text("[ape]\n", encoding="utf-8")

    child_dir = workspace_dir / "child"
    child_dir.mkdir()

    service = WorkspaceService(child_dir)

    assert service.workspace_dir == workspace_dir
    assert service.exists is True


def test_workspace_service_returns_none_when_workspace_is_missing(tmp_path) -> None:
    service = WorkspaceService(tmp_path)

    assert service.workspace_dir is None
    assert service.exists is False


def test_project_validation_service_reports_valid_project_state(tmp_path) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / ".ape").mkdir()
    (workspace_dir / ".ape" / "config.toml").write_text(
        '[ape]\nname = "demo"\n', encoding="utf-8"
    )

    project = Project.load(workspace_dir)
    service = ProjectValidationService(project)

    assert service.is_valid_project is True
    assert service.has_workspace is True
    assert service.has_config is True
    assert service.validation_errors == []


def test_project_validation_service_reports_missing_workspace_and_config(tmp_path) -> None:
    project = Project.load(tmp_path)
    service = ProjectValidationService(project)

    assert service.is_valid_project is False
    assert service.has_workspace is False
    assert service.has_config is False
    assert service.validation_errors == [
        "No workspace found.",
        "No project config found.",
    ]


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


def test_doctor_command_succeeds_and_prints_status() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "APE Environment Status" in result.output
    assert "python" in result.output.lower()
