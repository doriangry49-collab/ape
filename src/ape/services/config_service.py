from __future__ import annotations

import os

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

    # RFC-015: Planner Configurations
    @property
    def planner_provider(self) -> str:
        return os.environ.get("APE_PLANNER_PROVIDER") or self.config.get("ape", {}).get("planner", {}).get("provider", "openai")
        
    @property
    def planner_model(self) -> str:
        return os.environ.get("APE_PLANNER_MODEL") or self.config.get("ape", {}).get("planner", {}).get("model", "gpt-4o")

    @property
    def planner_api_key(self) -> str | None:
        return os.environ.get("APE_PLANNER_API_KEY") or self.config.get("ape", {}).get("planner", {}).get("api_key")

    @property
    def planner_base_url(self) -> str | None:
        return os.environ.get("APE_PLANNER_BASE_URL") or self.config.get("ape", {}).get("planner", {}).get("base_url")
