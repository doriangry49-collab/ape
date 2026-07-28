from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ape.intelligence.models import Opportunity


class BaseScanner(ABC):
    """Abstract base class/interface for opportunity signal scanners."""

    @abstractmethod
    def scan(self) -> list[Opportunity]:
        """Collect and return a list of normalized Opportunities."""
        pass
