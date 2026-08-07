"""
Executor Framework Base Contracts — EPIC-10B Specification.
Defines BaseExecutor protocol interface for local, docker, SSH, and GPU worker nodes.
"""

from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class BaseExecutor(Protocol):
    """Constitutional Protocol contract for Distributed Worker Executors."""

    node_type: str

    def prepare(self, task_payload: Dict[str, Any]) -> bool:
        """Prepare task execution environment."""
        ...

    def execute(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task and return execution payload results."""
        ...

    def health_check(self) -> bool:
        """Return executor node health status."""
        ...
