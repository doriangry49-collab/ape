from __future__ import annotations

from ape.project import Project
from ape.services.project_validation_service import ProjectValidationService
from ape.services.system_info_service import SystemInfoService


class DoctorService:
    """Lightweight read-only service that composes existing project & system diagnostics."""

    def __init__(
        self,
        project: Project,
        system_info_service: SystemInfoService | None = None
    ) -> None:
        self._project = project
        self._validation_service = ProjectValidationService(project)
        self._system_info_service = system_info_service or SystemInfoService()
        self._status = "unknown"
        self._warnings: list[str] = []
        self._errors: list[str] = []
        self._summary = ""

    @property
    def system_info(self) -> dict[str, str]:
        return self._system_info_service.status

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
