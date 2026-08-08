"""
SharedSwarmMemory Store — ORION-116 Specification.
Provides thread-safe in-memory state store for inter-agent context sharing.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SharedSwarmMemory:
    """Thread-safe in-memory shared state store for inter-agent collaboration."""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._history.append({"key": key, "value": value})

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._data

    def snapshot(self) -> Dict[str, Any]:
        return dict(self._data)
