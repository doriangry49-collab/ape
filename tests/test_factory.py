from ape.project import Project
from ape.services.factory import load_project


def test_load_project_returns_project_instance(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PWD", raising=False)
    
    (tmp_path / ".ape").mkdir()
    (tmp_path / ".ape" / "config.toml").write_text("[ape]\n", encoding="utf-8")
    
    project = load_project()
    assert isinstance(project, Project)
    assert project.root == tmp_path
