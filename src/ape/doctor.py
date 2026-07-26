import platform

from rich.console import Console
from rich.table import Table


def collect_environment_status() -> dict[str, str]:
    return {
        "package": "ape",
        "python": platform.python_version(),
        "platform": platform.platform(),
    }


def run_doctor(console: Console | None = None) -> None:
    console = console or Console()
    table = Table(title="APE Environment Status", show_header=False, box=None)
    table.add_column("Key", style="cyan")
    table.add_column("Value")

    for key, value in collect_environment_status().items():
        table.add_row(key, value)

    console.print(table)
