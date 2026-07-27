from __future__ import annotations

from pathlib import Path

from ape.workspace import find_workspace_dir


class WorkspaceService:
    """Lightweight read-only service for workspace discovery."""

    def __init__(self, start_dir: Path | None = None) -> None:
        self._start_dir = start_dir

    @property
    def workspace_dir(self) -> Path | None:
        return find_workspace_dir(self._start_dir)

    @property
    def exists(self) -> bool:
        return self.workspace_dir is not None

