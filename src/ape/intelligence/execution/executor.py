"""
Task Executor — abstract boundary + simulation-first MVP implementation.

DEFAULT = SIMULATION (dry_run=True).
Real shell execution is wired but NEVER the default in MVP.
No LLM provider dependency.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class TaskExecutor(ABC):
    """Abstract executor boundary. Engine talks only to this interface."""

    @abstractmethod
    def execute(self, task_description: str, deliverables: list[str]) -> str:
        """Execute a task. Returns a human-readable result string."""


class SimulationTaskExecutor(TaskExecutor):
    """
    MVP default executor — simulation mode.
    Prints what it would do; creates NO real files or processes.
    This is the ONLY executor used in Sprint 12 MVP.
    """

    def execute(self, task_description: str, deliverables: list[str]) -> str:
        return f"[SIMULATED] Would execute: {task_description}"


class ShellTaskExecutor(TaskExecutor):
    """
    Real shell executor — DISABLED by default in MVP.
    Only instantiated if caller explicitly requests it.
    Kept as interface-ready for future opt-in mechanism.
    """

    def execute(self, task_description: str, deliverables: list[str]) -> str:
        # Real implementation intentionally left as stub in MVP.
        # To enable: replace with subprocess.run logic behind explicit opt-in flag.
        raise NotImplementedError(
            "ShellTaskExecutor is not enabled in MVP. "
            "Use SimulationTaskExecutor (default) instead."
        )
