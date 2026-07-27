from typer.testing import CliRunner

from ape.doctor import run_doctor
from ape.project import Project
from ape.services import (
    DoctorService,
)

runner = CliRunner()

def test_doctor_service_reports_valid_project_state(tmp_path) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / ".ape").mkdir()
    (workspace_dir / ".ape" / "config.toml").write_text(
        '[ape]\nname = "demo"\n', encoding="utf-8"
    )

    project = Project.load(workspace_dir)
    service = DoctorService(project)

    run_result = service.run()

    assert run_result == {
        "status": "ok",
        "warnings": [],
        "errors": [],
        "summary": "Project validation passed.",
    }
    assert service.status == "ok"
    assert service.warnings == []
    assert service.errors == []
    assert service.summary == "Project validation passed."

def test_doctor_service_reports_invalid_project_state(tmp_path) -> None:
    project = Project.load(tmp_path)
    service = DoctorService(project)

    run_result = service.run()

    assert run_result == {
        "status": "invalid",
        "warnings": [],
        "errors": ["No workspace found.", "No project config found."],
        "summary": "Project validation failed.",
    }
    assert service.status == "invalid"
    assert service.warnings == []
    assert service.errors == ["No workspace found.", "No project config found."]
    assert service.summary == "Project validation failed."

def test_run_doctor_uses_the_provided_service() -> None:
    service_calls = []

    class StubService:
        def run(self) -> None:
            service_calls.append("run")

    run_doctor(StubService())

    assert service_calls == []

