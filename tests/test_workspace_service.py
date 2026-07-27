from typer.testing import CliRunner

from ape.services import (
    WorkspaceService,
)

runner = CliRunner()

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

