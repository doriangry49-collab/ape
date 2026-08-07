"""
Strategy-Based Retry Engine — ORION-113 Specification.
Provides RetryStrategy interface, ExponentialBackoffStrategy, LinearBackoffStrategy,
ImmediateRetryStrategy, NoRetryStrategy, and ProviderRetryOrchestrator.
"""

from dataclasses import dataclass
import random
import time
from typing import Any, Callable, Optional, Protocol, runtime_checkable

from ape.capabilities.contracts import CapabilityResult, ProviderTimeoutError, ProviderUnavailableError


@runtime_checkable
class RetryStrategy(Protocol):
    """Canonical RetryStrategy interface."""

    def calculate_delay_s(self, attempt: int) -> float:
        """Calculate backoff delay in seconds for given retry attempt index (1-indexed)."""
        ...


class ExponentialBackoffStrategy:
    """Exponential backoff retry strategy with jitter."""

    def __init__(self, base_delay_s: float = 0.5, max_delay_s: float = 10.0, jitter: bool = True) -> None:
        self.base_delay_s = base_delay_s
        self.max_delay_s = max_delay_s
        self.jitter = jitter

    def calculate_delay_s(self, attempt: int) -> float:
        delay = min(self.max_delay_s, self.base_delay_s * (2 ** (attempt - 1)))
        if self.jitter:
            delay += random.uniform(0, delay * 0.1)
        return round(delay, 3)


class LinearBackoffStrategy:
    """Linear backoff retry strategy."""

    def __init__(self, step_delay_s: float = 1.0, max_delay_s: float = 10.0) -> None:
        self.step_delay_s = step_delay_s
        self.max_delay_s = max_delay_s

    def calculate_delay_s(self, attempt: int) -> float:
        return min(self.max_delay_s, attempt * self.step_delay_s)


class ImmediateRetryStrategy:
    """Immediate retry strategy with zero delay."""

    def calculate_delay_s(self, attempt: int) -> float:
        return 0.0


class NoRetryStrategy:
    """Disables retries (raises exception immediately on first failure)."""

    def calculate_delay_s(self, attempt: int) -> float:
        return 0.0


class ProviderRetryOrchestrator:
    """Orchestrates retry loops using pluggable RetryStrategy instances."""

    def __init__(self, default_strategy: Optional[RetryStrategy] = None) -> None:
        self.default_strategy = default_strategy or ExponentialBackoffStrategy()

    def execute_with_retry(
        self,
        func: Callable[[], CapabilityResult],
        max_retries: int = 3,
        strategy: Optional[RetryStrategy] = None,
        on_retry: Optional[Callable[[int, Exception, float], None]] = None,
    ) -> CapabilityResult:
        retry_strat = strategy or self.default_strategy
        if isinstance(retry_strat, NoRetryStrategy):
            max_retries = 1

        last_exception: Optional[Exception] = None
        for attempt in range(1, max_retries + 1):
            try:
                return func()
            except Exception as exc:
                last_exception = exc
                if attempt >= max_retries:
                    break

                delay = retry_strat.calculate_delay_s(attempt)
                if on_retry:
                    try:
                        on_retry(attempt, exc, delay)
                    except Exception:
                        pass
                time.sleep(delay)

        if last_exception:
            raise last_exception
        raise ProviderUnavailableError("Retry loop exhausted without result.")
