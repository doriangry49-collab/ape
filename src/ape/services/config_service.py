from __future__ import annotations

from pathlib import Path

from ape.project import Project


class ConfigService:
    """Lightweight read-only service for project configuration access."""

    def __init__(self, project: Project) -> None:
        self._project = project

    @property
    def project_name(self) -> str | None:
        return self._project.name

    @property
    def config_exists(self) -> bool:
        return self._project.exists()

    @property
    def config(self) -> dict:
        return self._project.config

    @property
    def config_path(self) -> Path:
        return self._project.config_path
