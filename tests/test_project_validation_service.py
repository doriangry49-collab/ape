from typer.testing import CliRunner

from ape.project import Project
from ape.services import (
    ProjectValidationService,
)

runner = CliRunner()

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

