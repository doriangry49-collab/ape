from typer.testing import CliRunner

from ape.project import Project
from ape.services import (
    ConfigService,
)

runner = CliRunner()

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

