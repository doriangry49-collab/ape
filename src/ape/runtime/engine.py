"""
Production Execution Runtime Engine — ORION-109A Specification.
Provides generic execution resilience, exponential backoff retries, timeout bounds, cancellation tokens,
department-slug checkpointing (.build/ventures/{id}/checkpoints/{slug}.json), and runtime event hooks.
"""

from dataclasses import dataclass, field
import json
from pathlib import Path
import time
from typing import Any, Callable, Dict, List, Optional


@dataclass
class CancellationToken:
    """Token allowing safe cancellation of background execution tasks."""
    is_cancelled: bool = False

    def cancel(self) -> None:
        """Trigger cancellation signal."""
        self.is_cancelled = True


@dataclass
class RetryPolicy:
    """Exponential backoff retry policy for transient execution failures."""
    max_retries: int = 3
    initial_delay: float = 0.01  # Fast for unit testing
    backoff_factor: float = 2.0


@dataclass
class TimeoutPolicy:
    """Timeout bound policy for department task execution."""
    timeout_seconds: float = 30.0


@dataclass
class RuntimeEventHooks:
    """Event callbacks triggered during execution runtime step lifecycle."""
    on_step_started: Optional[Callable[[str, str], None]] = None
    on_step_finished: Optional[Callable[[str, str], None]] = None
    on_retry: Optional[Callable[[str, str, int, Exception], None]] = None
    on_timeout: Optional[Callable[[str, str, float], None]] = None
    on_checkpoint_saved: Optional[Callable[[str, str, Path], None]] = None
    on_execution_completed: Optional[Callable[[str], None]] = None


class CheckpointStore:
    """Manages department-slug checkpoint files inside .build/ventures/{venture_id}/checkpoints/."""

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self.root_dir = Path(root_dir) if root_dir else Path(".build/ventures")

    def get_checkpoint_path(self, venture_id: str, dept_slug: str) -> Path:
        """Return path to checkpoint file for a department slug."""
        return self.root_dir / venture_id / "checkpoints" / f"{dept_slug}.json"

    def save_checkpoint(self, venture_id: str, dept_slug: str, data: Dict[str, Any]) -> Path:
        """Save a department-slug checkpoint payload."""
        cp_path = self.get_checkpoint_path(venture_id, dept_slug)
        cp_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "venture_id": venture_id,
            "dept_slug": dept_slug,
            "saved_at": time.time(),
            "data": data,
        }
        cp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return cp_path

    def load_checkpoint(self, venture_id: str, dept_slug: str) -> Optional[Dict[str, Any]]:
        """Load a department-slug checkpoint payload if exists."""
        cp_path = self.get_checkpoint_path(venture_id, dept_slug)
        if not cp_path.exists():
            return None
        return json.loads(cp_path.read_text(encoding="utf-8"))

    def has_checkpoint(self, venture_id: str, dept_slug: str) -> bool:
        """Check if a checkpoint exists for a department slug."""
        return self.get_checkpoint_path(venture_id, dept_slug).exists()


class ExecutionRuntime:
    """
    Generic, resilient execution runtime wrapping department step execution with retries,
    timeout bounds, cancellation checks, checkpointing, and event triggers.
    """

    def __init__(
        self,
        retry_policy: Optional[RetryPolicy] = None,
        timeout_policy: Optional[TimeoutPolicy] = None,
        checkpoint_store: Optional[CheckpointStore] = None,
        events: Optional[RuntimeEventHooks] = None,
    ) -> None:
        self.retry_policy = retry_policy or RetryPolicy()
        self.timeout_policy = timeout_policy or TimeoutPolicy()
        self.checkpoint_store = checkpoint_store or CheckpointStore()
        self.events = events or RuntimeEventHooks()

    def run_step(
        self,
        venture_id: str,
        dept_slug: str,
        func: Callable[[], Any],
        cancellation_token: Optional[CancellationToken] = None,
    ) -> Any:
        """
        Execute generic department step with retry, timeout check, cancellation check,
        and department-slug checkpointing.
        """
        if cancellation_token and cancellation_token.is_cancelled:
            raise RuntimeError(f"Execution cancelled before step '{dept_slug}' for venture '{venture_id}'.")

        if self.events.on_step_started:
            self.events.on_step_started(venture_id, dept_slug)

        attempts = 0
        current_delay = self.retry_policy.initial_delay

        while attempts <= self.retry_policy.max_retries:
            if cancellation_token and cancellation_token.is_cancelled:
                raise RuntimeError(f"Execution cancelled during step '{dept_slug}' for venture '{venture_id}'.")

            attempts += 1
            step_start = time.time()

            try:
                result = func()

                # Check timeout policy
                elapsed = time.time() - step_start
                if elapsed > self.timeout_policy.timeout_seconds:
                    if self.events.on_timeout:
                        self.events.on_timeout(venture_id, dept_slug, self.timeout_policy.timeout_seconds)
                    raise TimeoutError(f"Step '{dept_slug}' exceeded timeout threshold of {self.timeout_policy.timeout_seconds}s.")

                # Save department-slug checkpoint
                checkpoint_data = {
                    "status": "COMPLETED",
                    "result_type": type(result).__name__,
                }
                cp_path = self.checkpoint_store.save_checkpoint(venture_id, dept_slug, checkpoint_data)

                if self.events.on_checkpoint_saved:
                    self.events.on_checkpoint_saved(venture_id, dept_slug, cp_path)

                if self.events.on_step_finished:
                    self.events.on_step_finished(venture_id, dept_slug)

                return result

            except Exception as exc:
                if attempts > self.retry_policy.max_retries:
                    raise exc

                if self.events.on_retry:
                    self.events.on_retry(venture_id, dept_slug, attempts, exc)

                time.sleep(current_delay)
                current_delay *= self.retry_policy.backoff_factor
