"""
Endpoint-Level CircuitBreaker Engine — ORION-113 Specification.
Provides ProviderEndpointKey and ProviderCircuitBreaker tracking circuit states (CLOSED, OPEN, HALF_OPEN)
at (provider_id, model) granular endpoint level.
"""

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Dict, Optional

from ape.capabilities.contracts import CircuitBreakerOpenError


@dataclass(frozen=True)
class ProviderEndpointKey:
    """Immutable endpoint identifier binding provider_id and model name."""
    provider_id: str
    model: str

    def __str__(self) -> str:
        return f"{self.provider_id}:{self.model}"


class CircuitBreakerState(str, Enum):
    """Circuit breaker state machine states."""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitStats:
    """Endpoint circuit state and failure counter metrics."""
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    consecutive_failures: int = 0
    last_state_change: float = field(default_factory=time.time)
    last_failure_time: float = 0.0


class ProviderCircuitBreaker:
    """
    Endpoint-level circuit breaker preventing cascading timeouts across AI provider models.
    Supports state transitions CLOSED -> OPEN -> HALF_OPEN -> CLOSED.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout_s: float = 30.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout_s = recovery_timeout_s
        self._endpoints: Dict[str, CircuitStats] = {}

    def _get_key_str(self, endpoint_key: ProviderEndpointKey) -> str:
        return str(endpoint_key)

    def get_state(self, endpoint_key: ProviderEndpointKey) -> CircuitBreakerState:
        k = self._get_key_str(endpoint_key)
        if k not in self._endpoints:
            self._endpoints[k] = CircuitStats()
        stats = self._endpoints[k]

        if stats.state == CircuitBreakerState.OPEN:
            if time.time() - stats.last_state_change >= self.recovery_timeout_s:
                stats.state = CircuitBreakerState.HALF_OPEN
                stats.last_state_change = time.time()

        return stats.state

    def check_execution_allowed(self, endpoint_key: ProviderEndpointKey) -> None:
        """Check if request execution is allowed; raises CircuitBreakerOpenError if OPEN."""
        state = self.get_state(endpoint_key)
        if state == CircuitBreakerState.OPEN:
            raise CircuitBreakerOpenError(
                f"CircuitBreaker is OPEN for endpoint '{endpoint_key}'. Request rejected to prevent cascading failure."
            )

    def record_success(self, endpoint_key: ProviderEndpointKey) -> None:
        """Record successful execution and reset circuit to CLOSED."""
        k = self._get_key_str(endpoint_key)
        if k not in self._endpoints:
            self._endpoints[k] = CircuitStats()
        stats = self._endpoints[k]

        stats.consecutive_failures = 0
        if stats.state != CircuitBreakerState.CLOSED:
            stats.state = CircuitBreakerState.CLOSED
            stats.last_state_change = time.time()

    def record_failure(self, endpoint_key: ProviderEndpointKey) -> None:
        """Record failure and trip circuit to OPEN if threshold exceeded."""
        k = self._get_key_str(endpoint_key)
        if k not in self._endpoints:
            self._endpoints[k] = CircuitStats()
        stats = self._endpoints[k]

        stats.consecutive_failures += 1
        stats.last_failure_time = time.time()

        if stats.consecutive_failures >= self.failure_threshold or stats.state == CircuitBreakerState.HALF_OPEN:
            stats.state = CircuitBreakerState.OPEN
            stats.last_state_change = time.time()
