from __future__ import annotations

import tomllib
from pathlib import Path
from types import MappingProxyType

from ape.workspace import find_workspace_dir


class Project:
    """Lightweight project abstraction for workspace-aware CLI commands."""

    def __init__(self, root: Path, config_path: Path) -> None:
        self._root = root
        self._config_path = config_path

    @property
    def root(self) -> Path:
        return self._root

    @property
    def config_path(self) -> Path:
        return self._config_path

    @property
    def config(self) -> dict:
        if not self.config_path.exists():
            return {}

        with self.config_path.open("rb") as handle:
            return tomllib.load(handle)

    @property
    def name(self) -> str | None:
        config = self.config
        ape_config = config.get("ape", {})
        if not isinstance(ape_config, dict):
            return None
        name = ape_config.get("name")
        return name if isinstance(name, str) else None

    @property
    def info(self) -> MappingProxyType:
        return MappingProxyType(
            {
                "root": self.root,
                "config_path": self.config_path,
                "exists": self.exists(),
                "name": self.name,
            }
        )

    @property
    def metadata(self) -> dict[str, object]:
        return dict(self.info)

    @classmethod
    def load(cls, path: Path | None = None) -> "Project":
        start_dir = (path or Path.cwd()).resolve()
        root = find_workspace_dir(start_dir) or start_dir
        config_path = root / ".ape" / "config.toml"
        return cls(root=root, config_path=config_path)

    def exists(self) -> bool:
        return self.config_path.exists()
