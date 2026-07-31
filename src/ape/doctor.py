from rich.console import Console
from rich.table import Table

from ape.services import DoctorService, SystemInfoService


def collect_environment_status(service: SystemInfoService | None = None) -> dict[str, str]:
    info_service = service or SystemInfoService()
    return info_service.status


def run_doctor(service: DoctorService, console: Console | None = None) -> None:
    console = console or Console()

    table = Table(title="APE Environment Status", show_header=False, box=None)
    table.add_column("Key", style="cyan")
    table.add_column("Value")

    env_status = service.system_info if hasattr(service, "system_info") else collect_environment_status()

    for key, value in env_status.items():
        table.add_row(key, str(value))

    console.print(table)
