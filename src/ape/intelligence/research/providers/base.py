from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseResearchProvider(ABC):
    """Abstract base class/interface for research signal providers."""

    @abstractmethod
    def fetch_signals(self, topic: str) -> dict[str, Any]:
        """Fetch and normalize research signals for the given topic."""
        pass
