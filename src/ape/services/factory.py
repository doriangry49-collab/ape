from __future__ import annotations

from pathlib import Path

from ape.project import Project


def load_project(start_dir: Path | None = None) -> Project:
    """Single entry point for loading a Project instance."""
    return Project.load(start_dir)
