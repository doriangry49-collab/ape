from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

from ape.project import Project


class ProjectInfoService:
    """Lightweight read-only service for project information access."""

    def __init__(self, project: Project) -> None:
        self._project = project

    @property
    def root(self) -> Path:
        return self._project.root

    @property
    def config_path(self) -> Path:
        return self._project.config_path

    @property
    def exists(self) -> bool:
        return self._project.exists()

    @property
    def name(self) -> str | None:
        return self._project.name

    @property
    def info(self) -> MappingProxyType:
        return self._project.info

    @property
    def metadata(self) -> dict[str, object]:
        return self._project.metadata

    @property
    def config(self) -> dict:
        return self._project.config
