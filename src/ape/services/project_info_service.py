from __future__ import annotations

import os
from pathlib import Path
from types import MappingProxyType

from ape.project import Project
from ape.services.config_service import ConfigService
from ape.services.workspace_service import WorkspaceService


class ProjectInfoService:
    """Lightweight read-only service for project information access."""

    def __init__(self, project: Project) -> None:
        self._project = project
        self._config_service = ConfigService(project)
        self._workspace_service = WorkspaceService(project.root)

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

    def initialize_workspace(
        self,
        current_dir: Path,
        project_root: Path,
        pwd: str | None = None,
    ) -> tuple[Path, Path, Path, bool]:
        target_dir = self._workspace_service.resolve_target_directory(
            current_dir,
            project_root,
            pwd or os.environ.get("PWD"),
        )
        project = Project.load(target_dir)
        target_root = project.root
        ape_dir = target_root / ".ape"
        ape_dir.mkdir(parents=True, exist_ok=True)
        config_path = ape_dir / "config.toml"
        created = not config_path.exists()
        if created:
            config_path.write_text("[ape]\n", encoding="utf-8")
        return target_root, ape_dir, config_path, created
