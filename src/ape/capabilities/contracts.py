"""
Capabilities Contracts & Exception Hierarchy — ORION-111B / ORION-112 / ORION-113 / ORION-114 Specification.
Defines CapabilityError hierarchy, ExecutionPolicy, ExecutionContext, RuntimeContext,
FinishReason, CacheSource, CapabilityResult, ExecutionState, and unified ExecutionResult.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional

from ape.capabilities.artifacts import ExecutionArtifact


class CapabilityError(Exception):
    """Base exception for all capability and provider execution errors."""
    pass


class ProviderUnavailableError(CapabilityError):
    """Raised when no healthy provider is available for the requested capability."""
    pass


class CapabilityNotSupportedError(CapabilityError):
    """Raised when requested capability_id is not registered."""
    pass


class BudgetExceededError(CapabilityError):
    """Raised when execution usage exceeds ExecutionBudget limits."""
    pass


class ProviderTimeoutError(CapabilityError):
    """Raised when provider request exceeds execution timeout limit."""
    pass


class PolicyDeniedError(CapabilityError):
    """Raised when requested action violates ExecutionPolicy rules."""
    pass


class CircuitBreakerOpenError(ProviderUnavailableError):
    """Raised when request is blocked by an OPEN CircuitBreaker."""
    pass


class FinishReason(str, Enum):
    """Normalized provider execution completion reason."""
    STOP = "stop"
    MAX_TOKENS = "max_tokens"
    CONTENT_FILTER = "content_filter"
    TOOL_CALL = "tool_call"
    TIMEOUT = "timeout"
    ERROR = "error"
    CANCELLED = "cancelled"


class CacheSource(str, Enum):
    """Execution payload cache source indicator."""
    NONE = "none"
    MEMORY = "memory"
    DISK = "disk"
    REDIS = "redis"
    SEMANTIC = "semantic"
    PROVIDER = "provider"


@dataclass(frozen=True)
class ExecutionContext:
    """Immutable execution context identity value object."""
    execution_id: str
    venture_id: str
    trace_id: str
    workspace_id: str
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class RuntimeContext:
    """Dynamic execution runtime context state tracking attempt counts, timings, and selected models."""
    execution_id: str
    trace_id: str
    attempt: int = 1
    retry_count: int = 0
    selected_provider_id: str = ""
    selected_model: str = ""
    circuit_state: str = "CLOSED"
    started_at: float = field(default_factory=time.time)
    deadline: Optional[float] = None
    timeout_ms: float = 60000.0
    telemetry: Dict[str, Any] = field(default_factory=dict)

    @property
    def elapsed_ms(self) -> float:
        return round((time.time() - self.started_at) * 1000.0, 2)


@dataclass(frozen=True)
class ExecutionPolicy:
    """Decoupled policy rules governing capability execution."""
    retry_limit: int = 3
    timeout_ms: float = 30000.0
    cache_allowed: bool = True
    streaming_allowed: bool = False
    reasoning_allowed: bool = True
    max_parallel_calls: int = 5
    required_features: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CapabilityResult:
    """Standardized normalized execution result produced by all ProviderAdapters."""
    success: bool
    provider_id: str
    model: str
    capability_id: str
    duration_ms: float
    provider_version: str = "1.0.0"
    finish_reason: FinishReason = FinishReason.STOP
    cache_source: CacheSource = CacheSource.NONE
    trace_id: str = ""
    prompt_trace_id: str = ""
    cost: float = 0.00
    token_usage: Dict[str, int] = field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    provider_attempts: List[str] = field(default_factory=list)


@dataclass
class ExecutionState:
    """Immutable functional pipeline execution state passed between stages."""
    context: ExecutionContext
    runtime: RuntimeContext
    capability_id: str
    rendered_prompt: Any
    selected_provider: Any = None
    candidates: List[Any] = field(default_factory=list)
    result: Optional[CapabilityResult] = None
    trace_events: List[Any] = field(default_factory=list)
    artifacts: List[ExecutionArtifact] = field(default_factory=list)
    working_memory: Dict[str, Any] = field(default_factory=dict)


class ExecutionResult:
    """Unified execution response object providing final(), stream(), and trace()."""

    def __init__(self, capability_result: CapabilityResult, trace: Any = None, chunks: Optional[List[Any]] = None) -> None:
        self._result = capability_result
        self._trace = trace
        self._chunks = chunks or []

    def final(self) -> CapabilityResult:
        """Return final normalized CapabilityResult."""
        return self._result

    def stream(self) -> Iterator[Any]:
        """Return iterator over streamed chunks."""
        return iter(self._chunks)

    def trace(self) -> Any:
        """Return event-sourced ExecutionTrace."""
        return self._trace
