from pathlib import Path


def find_workspace_dir(start_dir: Path | None = None) -> Path | None:
    """Discover an APE workspace by searching upward for .ape/config.toml."""
    current_dir = (start_dir or Path.cwd()).resolve()

    for directory in [current_dir, *current_dir.parents]:
        config_path = directory / ".ape" / "config.toml"
        if config_path.exists():
            return directory

    return None
