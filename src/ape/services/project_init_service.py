from __future__ import annotations

from pathlib import Path

from ape.project import Project


class ProjectInitializationService:
    """Service dedicated to workspace initialization and creation."""

    def initialize_workspace(
        self,
        current_dir: Path,
        project_root: Path,
    ) -> tuple[Path, Path, Path, bool]:
        project = Project.load(current_dir)
        target_root = project.root
        ape_dir = target_root / ".ape"
        ape_dir.mkdir(parents=True, exist_ok=True)
        config_path = ape_dir / "config.toml"
        created = not config_path.exists()
        if created:
            config_path.write_text("[ape]\n", encoding="utf-8")
        return target_root, ape_dir, config_path, created
