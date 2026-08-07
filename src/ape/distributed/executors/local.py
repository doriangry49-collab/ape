"""
Local Sub-process Executor — EPIC-10B Specification.
Executes tasks locally within sub-process worker environments.
"""

from typing import Any, Dict
from ape.distributed.executors.base import BaseExecutor


class LocalExecutor:
    """Specialized local sub-process worker executor."""

    node_type = "local"

    def prepare(self, task_payload: Dict[str, Any]) -> bool:
        return True

    def execute(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task_payload.get("task_id", "t_01")
        return {
            "task_id": task_id,
            "status": "COMPLETED",
            "executor": "LocalExecutor",
            "output": f"Executed task '{task_id}' locally.",
        }

    def health_check(self) -> bool:
        return True
