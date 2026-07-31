from __future__ import annotations

import platform
from typing import Dict


class SystemInfoService:
    """Lightweight read-only service for system and environment diagnostics."""

    def collect_system_info(self) -> dict[str, str]:
        """Collects environment diagnostic information dictionary."""
        return {
            "package": "ape",
            "python": platform.python_version(),
            "platform": platform.platform(),
        }

    @property
    def status(self) -> dict[str, str]:
        return self.collect_system_info()
