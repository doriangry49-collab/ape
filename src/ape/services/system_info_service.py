from __future__ import annotations

import platform


class SystemInfoService:
    """Lightweight read-only service for system and environment diagnostics."""

    @property
    def status(self) -> dict[str, str]:
        return {
            "package": "ape",
            "python": platform.python_version(),
            "platform": platform.platform(),
        }
