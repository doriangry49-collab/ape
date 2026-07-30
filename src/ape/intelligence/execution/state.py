"""
Task State Machine — centralises all status transitions.

Every state change MUST go through this class.
No task.status assignment is allowed outside TaskStateMachine.
"""
from __future__ import annotations

from ape.intelligence.execution.models import ExecutionTask, TaskStatus


class InvalidTransitionError(Exception):
    pass


# Valid transitions: from_status -> set of allowed to_status
_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING: {
        TaskStatus.IN_PROGRESS, TaskStatus.REQUIRES_APPROVAL, TaskStatus.BLOCKED
    },
    TaskStatus.IN_PROGRESS: {
        TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.PAUSED,
        TaskStatus.REQUIRES_APPROVAL, TaskStatus.BLOCKED
    },
    TaskStatus.FAILED:             {TaskStatus.IN_PROGRESS},
    TaskStatus.PAUSED:             {TaskStatus.IN_PROGRESS},
    TaskStatus.REQUIRES_APPROVAL:  {TaskStatus.IN_PROGRESS, TaskStatus.DENIED},
    TaskStatus.BLOCKED:            set(),  # terminal state if docker missing, requires restart
    TaskStatus.COMPLETED:          set(),  # terminal
    TaskStatus.DENIED:             set(),  # terminal
}


class TaskStateMachine:
    def __init__(self, task: ExecutionTask) -> None:
        self._task = task

    def _transition(self, new_status: TaskStatus) -> None:
        current = self._task.status
        if new_status not in _TRANSITIONS.get(current, set()):
            raise InvalidTransitionError(
                f"Cannot transition {current.value} -> {new_status.value}"
            )
        self._task.status = new_status

    def start(self) -> None:
        """PENDING / PAUSED -> IN_PROGRESS."""
        self._transition(TaskStatus.IN_PROGRESS)

    def complete(self) -> None:
        self._transition(TaskStatus.COMPLETED)

    def fail(self, error: str = "") -> None:
        self._task.error = error
        self._transition(TaskStatus.FAILED)

    def block(self, reason: str = "") -> None:
        self._task.error = reason
        self._transition(TaskStatus.BLOCKED)

    def retry(self) -> None:
        """FAILED -> IN_PROGRESS."""
        self._transition(TaskStatus.IN_PROGRESS)

    def pause(self) -> None:
        self._transition(TaskStatus.PAUSED)

    def resume(self) -> None:
        """PAUSED -> IN_PROGRESS."""
        self._transition(TaskStatus.IN_PROGRESS)

    def request_approval(self) -> None:
        self._transition(TaskStatus.REQUIRES_APPROVAL)

    def approve(self) -> None:
        """REQUIRES_APPROVAL -> IN_PROGRESS (user said Y)."""
        self._transition(TaskStatus.IN_PROGRESS)

    def deny(self, reason: str = "") -> None:
        """REQUIRES_APPROVAL -> DENIED (user said N — terminal)."""
        if reason:
            self._task.error = reason
        self._transition(TaskStatus.DENIED)
