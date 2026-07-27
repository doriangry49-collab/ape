from typer.testing import CliRunner

from ape.workspace import find_workspace_dir

runner = CliRunner()

def test_find_workspace_dir_discovers_workspace_from_child_directory(tmp_path) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / ".ape").mkdir()
    (workspace_dir / ".ape" / "config.toml").write_text("[ape]\n", encoding="utf-8")

    child_dir = workspace_dir / "child"
    child_dir.mkdir()

    assert find_workspace_dir(child_dir) == workspace_dir

