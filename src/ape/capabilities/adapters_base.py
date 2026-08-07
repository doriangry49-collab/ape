"""
ProviderAdapter Protocol & Lifecycle Base Specification — ORION-111B / ORION-112 / ORION-113.
Defines ProviderHealth, ProviderHealthMonitor, ProviderProfile, ProviderFeatureSet,
standardized ProviderAdapter Protocol lifecycle methods, and MockProviderAdapter.
"""

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ape.capabilities.config import ProviderFeatureSet
from ape.capabilities.contracts import CacheSource, CapabilityResult, ExecutionContext, FinishReason
from ape.prompts.template import RenderedPrompt


class ProviderHealth(str, Enum):
    """Provider health status enum."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    RATE_LIMITED = "rate_limited"


class ProviderHealthMonitor:
    """Dynamic provider health monitor tracking rolling latency, error rates, and heartbeats."""

    def __init__(self, provider_id: str, consecutive_failure_threshold: int = 5) -> None:
        self.provider_id = provider_id
        self.consecutive_failure_threshold = consecutive_failure_threshold
        self.total_calls: int = 0
        self.successful_calls: int = 0
        self.failed_calls: int = 0
        self.consecutive_failures: int = 0
        self.last_heartbeat: float = time.time()
        self.latencies_ms: List[float] = []

    def record_success(self, latency_ms: float) -> None:
        self.total_calls += 1
        self.successful_calls += 1
        self.consecutive_failures = 0
        self.last_heartbeat = time.time()
        self.latencies_ms.append(latency_ms)
        if len(self.latencies_ms) > 100:
            self.latencies_ms.pop(0)

    def record_failure(self, is_rate_limit: bool = False) -> None:
        self.total_calls += 1
        self.failed_calls += 1
        self.consecutive_failures += 1
        self.last_heartbeat = time.time()

    def get_health(self) -> ProviderHealth:
        if self.consecutive_failures >= self.consecutive_failure_threshold:
            return ProviderHealth.OFFLINE
        if self.consecutive_failures >= 1:
            return ProviderHealth.DEGRADED
        return ProviderHealth.HEALTHY

    @property
    def avg_latency_ms(self) -> float:
        return sum(self.latencies_ms) / len(self.latencies_ms) if self.latencies_ms else 50.0

    @property
    def error_rate(self) -> float:
        return (self.failed_calls / self.total_calls) if self.total_calls > 0 else 0.0


@dataclass(frozen=True)
class ProviderProfile:
    """Immutable provider profile metadata descriptor."""
    provider_id: str
    display_name: str
    vendor: str
    provider_version: str = "1.0.0"
    supports_streaming: bool = False
    supports_tools: bool = False
    supports_images: bool = False
    supports_reasoning: bool = True
    max_context_tokens: int = 128000
    cost_per_1k_tokens: float = 0.002
    health: ProviderHealth = ProviderHealth.HEALTHY
    features: ProviderFeatureSet = field(default_factory=ProviderFeatureSet)


@runtime_checkable
class ProviderAdapter(Protocol):
    """Canonical ProviderAdapter Protocol matching frozen ORION-111B / ORION-112 / ORION-113 lifecycle contract."""

    @property
    def provider_id(self) -> str:
        ...

    @property
    def profile(self) -> ProviderProfile:
        ...

    def features(self) -> ProviderFeatureSet:
        """Return ProviderFeatureSet descriptor."""
        ...

    def supports(self, feature_name: str) -> bool:
        """Check if feature_name is supported by provider."""
        ...

    def prepare(self, rendered_prompt: RenderedPrompt, capability_id: str) -> Dict[str, Any]:
        """Prepare request payload dictionary."""
        ...

    def execute(
        self,
        rendered_prompt: RenderedPrompt,
        capability_id: str,
        context: ExecutionContext,
    ) -> CapabilityResult:
        """Execute request and return CapabilityResult."""
        ...

    def normalize(self, raw_response: Any, capability_id: str, context: ExecutionContext, duration_ms: float) -> CapabilityResult:
        """Normalize raw provider payload into standardized CapabilityResult."""
        ...

    def estimate_cost(self, token_count: int) -> float:
        """Estimate execution cost for token count."""
        ...

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text payload."""
        ...

    def health(self) -> ProviderHealth:
        """Check current ProviderHealth status."""
        ...


class MockProviderAdapter:
    """Built-in MockProviderAdapter implementing full ProviderAdapter lifecycle contract and health monitor."""

    def __init__(
        self,
        provider_id: str = "mock",
        display_name: str = "Mock LLM Provider",
        vendor: str = "APE Internal",
        cost_per_1k_tokens: float = 0.001,
        health_status: ProviderHealth = ProviderHealth.HEALTHY,
        features: Optional[ProviderFeatureSet] = None,
    ) -> None:
        self._provider_id = provider_id
        self._health_monitor = ProviderHealthMonitor(provider_id)
        self._features = features or ProviderFeatureSet()
        self._profile = ProviderProfile(
            provider_id=provider_id,
            display_name=display_name,
            vendor=vendor,
            provider_version="1.0.0",
            cost_per_1k_tokens=cost_per_1k_tokens,
            health=health_status,
            features=self._features,
        )

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def profile(self) -> ProviderProfile:
        return self._profile

    def features(self) -> ProviderFeatureSet:
        return self._features

    def supports(self, feature_name: str) -> bool:
        return self._features.supports(feature_name)

    def prepare(self, rendered_prompt: RenderedPrompt, capability_id: str) -> Dict[str, Any]:
        return {
            "provider_id": self._provider_id,
            "capability_id": capability_id,
            "system_prompt": rendered_prompt.system_prompt,
            "user_prompt": rendered_prompt.user_prompt,
            "trace_id": rendered_prompt.trace_id,
        }

    def estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def estimate_cost(self, token_count: int) -> float:
        return round((token_count / 1000.0) * self._profile.cost_per_1k_tokens, 6)

    def health(self) -> ProviderHealth:
        monitor_health = self._health_monitor.get_health()
        return monitor_health if monitor_health != ProviderHealth.HEALTHY else self._profile.health

    def normalize(self, raw_response: Any, capability_id: str, context: ExecutionContext, duration_ms: float) -> CapabilityResult:
        output_text = raw_response.get("response_text", "") if isinstance(raw_response, dict) else str(raw_response)
        tokens = self.estimate_tokens(output_text) + 150
        cost = self.estimate_cost(tokens)

        return CapabilityResult(
            success=True,
            provider_id=self._provider_id,
            model="mock-v1",
            capability_id=capability_id,
            duration_ms=duration_ms,
            provider_version=self._profile.provider_version,
            finish_reason=FinishReason.STOP,
            cache_source=CacheSource.NONE,
            trace_id=context.trace_id,
            prompt_trace_id="",
            cost=cost,
            token_usage={"prompt_tokens": 150, "completion_tokens": tokens - 150, "total_tokens": tokens},
            raw_payload={"response_text": output_text},
        )

    def execute(
        self,
        rendered_prompt: RenderedPrompt,
        capability_id: str,
        context: ExecutionContext,
    ) -> CapabilityResult:
        start_time = time.time()
        payload = self.prepare(rendered_prompt, capability_id)
        raw_res = {"response_text": f"[MOCK OUTPUT for {capability_id}] Payload trace '{rendered_prompt.trace_id}' executed."}
        duration_ms = round((time.time() - start_time) * 1000 + 10, 2)
        res = self.normalize(raw_res, capability_id, context, duration_ms)
        self._health_monitor.record_success(duration_ms)

        return CapabilityResult(
            success=res.success,
            provider_id=res.provider_id,
            model=res.model,
            capability_id=res.capability_id,
            duration_ms=res.duration_ms,
            provider_version=res.provider_version,
            finish_reason=res.finish_reason,
            cache_source=res.cache_source,
            trace_id=res.trace_id,
            prompt_trace_id=rendered_prompt.trace_id,
            cost=res.cost,
            token_usage=res.token_usage,
            raw_payload=res.raw_payload,
        )
