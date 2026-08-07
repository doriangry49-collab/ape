"""
Base Runtime Pack Interface — RFC-022 / PR-E1 Specification.
Provides abstract BaseRuntimePack interface for multi-language execution verification.
"""

from abc import ABC, abstractmethod
from typing import Any, Tuple

from ape.quality.contracts import ValidationContext


class BaseRuntimePack(ABC):
    """
    Abstract interface for language-specific runtime packs.
    Decouples language-specific process lifecycle and HTTP probing from RuntimeValidator.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name identifier of the runtime pack (e.g. 'python', 'node', 'go', 'rust', 'docker')."""
        ...

    @abstractmethod
    def prepare(self, context: ValidationContext) -> None:
        """Prepare build artifacts, virtualenvs, or dependencies prior to launching."""
        ...

    @abstractmethod
    def launch(self, context: ValidationContext) -> Any:
        """Launch application process or container in background."""
        ...

    @abstractmethod
    def probe(self, context: ValidationContext) -> Tuple[bool, str]:
        """Perform HTTP health check, TCP probe, or exit code assertion. Returns (passed, message)."""
        ...

    @abstractmethod
    def shutdown(self) -> None:
        """Clean up spawned process, container, or background threads."""
        ...
