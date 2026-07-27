import pytest
from typer.testing import CliRunner

from ape.project import Project

runner = CliRunner()

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

