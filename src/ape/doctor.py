from rich.console import Console
from rich.table import Table

from ape.services import DoctorService, SystemInfoService


def collect_environment_status() -> dict[str, str]:
    service = SystemInfoService()
    return service.status


def run_doctor(service: DoctorService, console: Console | None = None) -> None:
    console = console or Console()

    table = Table(title="APE Environment Status", show_header=False, box=None)
    table.add_column("Key", style="cyan")
    table.add_column("Value")

    for key, value in collect_environment_status().items():
        table.add_row(key, value)

    console.print(table)
