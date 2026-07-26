import typer

from ape.doctor import run_doctor

app = typer.Typer(help="APE foundation CLI")


@app.callback()
def main() -> None:
    """APE foundation CLI."""


@app.command("doctor")
def doctor() -> None:
    """Show a simple environment status."""
    run_doctor()


if __name__ == "__main__":
    app()
