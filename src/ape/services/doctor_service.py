from __future__ import annotations

from ape.project import Project
from ape.services.config_service import ConfigService
from ape.services.project_validation_service import ProjectValidationService
from ape.services.workspace_service import WorkspaceService


class DoctorService:
    """Lightweight read-only service that composes existing project diagnostics."""

    def __init__(self, project: Project) -> None:
        self._project = project
        self._config_service = ConfigService(project)
        self._workspace_service = WorkspaceService(project.root)
        self._validation_service = ProjectValidationService(project)
        self._status = "unknown"
        self._warnings: list[str] = []
        self._errors: list[str] = []
        self._summary = ""

    @property
    def status(self) -> str:
        return self._status

    @property
    def warnings(self) -> list[str]:
        return self._warnings

    @property
    def errors(self) -> list[str]:
        return self._errors

    @property
    def summary(self) -> str:
        return self._summary

    def run(self) -> dict[str, object]:
        self._errors = list(self._validation_service.validation_errors)
        self._warnings = []

        if self._errors:
            self._status = "invalid"
            self._summary = "Project validation failed."
        else:
            self._status = "ok"
            self._summary = "Project validation passed."

        return {
            "status": self._status,
            "warnings": self._warnings,
            "errors": self._errors,
            "summary": self._summary,
        }
