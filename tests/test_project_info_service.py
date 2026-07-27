import inspect

import pytest
from typer.testing import CliRunner

from ape.project import Project
from ape.services import ProjectInfoService

runner = CliRunner()


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


def test_project_info_service_does_not_hold_config_or_workspace_dependencies() -> None:
    """ProjectInfoService should only delegate to Project directly.
    ConfigService and WorkspaceService are dead dependencies — this test
    enforces their removal from the constructor.
    """
    from ape.services.project_info_service import ProjectInfoService as PIS

    init_source = inspect.getsource(PIS.__init__)
    assert "ConfigService" not in init_source, (
        "ProjectInfoService.__init__ must not instantiate ConfigService"
    )
    assert "WorkspaceService" not in init_source, (
        "ProjectInfoService.__init__ must not instantiate WorkspaceService"
    )
