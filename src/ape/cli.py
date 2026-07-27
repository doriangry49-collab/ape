from pathlib import Path

import typer

from ape import __version__
from ape.doctor import run_doctor
from ape.project import Project
from ape.services import (
    ConfigService,
    DoctorService,
    ProjectInfoService,
    ProjectInitializationService,
    ProjectValidationService,
)

app = typer.Typer(help="APE foundation CLI")


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

    init_service = ProjectInitializationService()
    target_root, ape_dir, config_path, created = init_service.initialize_workspace(
        current_dir=current_dir,
        project_root=project_root,
    )

    typer.echo(f"Created {ape_dir.relative_to(target_root)}/")
    if created:
        typer.echo(f"Created {config_path.relative_to(target_root)}")
    else:
        typer.echo(f"Using existing {config_path.relative_to(target_root)}")


@app.command("config")
def config() -> None:
    """Show the current APE workspace configuration details."""
    project = Project.load()
    info_service = ProjectInfoService(project)
    validation_service = ProjectValidationService(project)
    config_service = ConfigService(project)

    if not validation_service.has_workspace or not validation_service.has_config:
        typer.echo("Error: no APE workspace found")
        raise typer.Exit(code=1)

    typer.echo(f"Workspace: {info_service.root}")
    typer.echo(f"Config: {config_service.config_path}")
    typer.echo("Status: OK")


@app.command("doctor")
def doctor() -> None:
    """Show a simple environment status."""
    project = Project.load()
    service = DoctorService(project)
    service.run()
    run_doctor(service=service)


if __name__ == "__main__":
    app()
