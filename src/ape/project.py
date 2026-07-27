from __future__ import annotations

from pathlib import Path

from ape.workspace import find_workspace_dir


class Project:
    """Lightweight project abstraction for workspace-aware CLI commands."""

    def __init__(self, root: Path, config_path: Path) -> None:
        self.root = root
        self.config_path = config_path

    @classmethod
    def load(cls, path: Path | None = None) -> "Project":
        start_dir = (path or Path.cwd()).resolve()
        root = find_workspace_dir(start_dir) or start_dir
        config_path = root / ".ape" / "config.toml"
        return cls(root=root, config_path=config_path)

    def exists(self) -> bool:
        return self.config_path.exists()
