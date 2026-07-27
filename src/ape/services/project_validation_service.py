from __future__ import annotations

from ape.project import Project
from ape.services.config_service import ConfigService
from ape.services.workspace_service import WorkspaceService


class ProjectValidationService:
    """Lightweight read-only service for validating project state."""

    def __init__(self, project: Project) -> None:
        self._project = project
        self._config_service = ConfigService(project)
        self._workspace_service = WorkspaceService(project.root)

    @property
    def is_valid_project(self) -> bool:
        return not self.validation_errors

    @property
    def has_workspace(self) -> bool:
        return self._workspace_service.exists

    @property
    def has_config(self) -> bool:
        return self._config_service.config_exists

    @property
    def validation_errors(self) -> list[str]:
        errors: list[str] = []

        if not self.has_workspace:
            errors.append("No workspace found.")

        if not self.has_config:
            errors.append("No project config found.")

        return errors
