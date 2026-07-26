import os
from pathlib import Path

import typer

from ape import __version__
from ape.doctor import run_doctor

app = typer.Typer(help="APE foundation CLI")


def find_workspace_dir(start_dir: Path | None = None) -> Path | None:
    """Discover an APE workspace by searching upward for .ape/config.toml."""
    current_dir = (start_dir or Path.cwd()).resolve()

    for directory in [current_dir, *current_dir.parents]:
        config_path = directory / ".ape" / "config.toml"
        if config_path.exists():
            return directory

    return None


@app.callback()
def main() -> None:
    """APE foundation CLI."""


@app.command("version")
def version() -> None:
    """Print the current package version."""
    typer.echo(__version__)


@app.command("init")
def init() -> None:
    """Initialize a minimal APE workspace in the target directory."""
    current_dir = Path.cwd().resolve()
    project_root = Path(__file__).resolve().parents[2]

    target_dir = current_dir
    pwd = os.environ.get("PWD")
    if current_dir == project_root and pwd:
        candidate_dir = Path(pwd).expanduser().resolve()
        if candidate_dir.exists() and candidate_dir.is_dir():
            target_dir = candidate_dir

    discovered_workspace = find_workspace_dir(target_dir)
    if discovered_workspace is not None:
        target_dir = discovered_workspace

    ape_dir = target_dir / ".ape"
    ape_dir.mkdir(parents=True, exist_ok=True)
    typer.echo(f"Created {ape_dir.relative_to(target_dir)}/")

    config_path = ape_dir / "config.toml"
    if not config_path.exists():
        config_path.write_text("[ape]\n", encoding="utf-8")
        typer.echo(f"Created {config_path.relative_to(target_dir)}")
    else:
        typer.echo(f"Using existing {config_path.relative_to(target_dir)}")


@app.command("config")
def config() -> None:
    """Show the current APE workspace configuration details."""
    workspace_dir = find_workspace_dir()

    if workspace_dir is None:
        typer.echo("Error: no APE workspace found")
        raise typer.Exit(code=1)

    config_path = workspace_dir / ".ape" / "config.toml"
    typer.echo(f"Workspace: {workspace_dir}")
    typer.echo(f"Config: {config_path}")
    typer.echo("Status: OK")


@app.command("doctor")
def doctor() -> None:
    """Show a simple environment status."""
    run_doctor()


if __name__ == "__main__":
    app()
