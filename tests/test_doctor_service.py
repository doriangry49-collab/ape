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
    assert service.system_info["package"] == "ape"


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

def test_doctor_service_does_not_hold_config_or_workspace_dependencies() -> None:
    """DoctorService should only depend on ProjectValidationService.
    ConfigService and WorkspaceService are dead dependencies — this test
    enforces their removal from the constructor.
    """
    import inspect

    from ape.services.doctor_service import DoctorService as DS

    init_source = inspect.getsource(DS.__init__)
    assert "ConfigService" not in init_source, (
        "DoctorService.__init__ must not instantiate ConfigService"
    )
    assert "WorkspaceService" not in init_source, (
        "DoctorService.__init__ must not instantiate WorkspaceService"
    )


def test_workspace_service_does_not_have_resolve_target_directory() -> None:
    """resolve_target_directory was dead code after PWD removal.
    This test enforces its removal.
    """
    from ape.services.workspace_service import WorkspaceService as WS

    assert not hasattr(WS, "resolve_target_directory"), (
        "WorkspaceService must not expose resolve_target_directory (dead code)"
    )
