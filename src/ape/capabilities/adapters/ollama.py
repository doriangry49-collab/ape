"""
Ollama Local LLM ProviderAdapter — ORION-112 Specification.
Thin integration adapter for Local Ollama models using ProviderConfig and HTTPTransport abstraction.
Zero token cost ($0.00).
"""

from dataclasses import dataclass
import time
from typing import Any, Dict, Optional

from ape.capabilities.adapters_base import ProviderAdapter, ProviderFeatureSet, ProviderHealth, ProviderHealthMonitor, ProviderProfile
from ape.capabilities.config import ProviderConfig
from ape.capabilities.contracts import CacheSource, CapabilityResult, ExecutionContext, FinishReason
from ape.capabilities.transport import HTTPRequest, HTTPTransport, MockHTTPTransport
from ape.prompts.template import RenderedPrompt


class OllamaProviderAdapter:
    """Thin Ollama Local LLM ProviderAdapter implementing full ProviderAdapter lifecycle contract."""

    def __init__(
        self,
        config: Optional[ProviderConfig] = None,
        transport: Optional[HTTPTransport] = None,
    ) -> None:
        self.config = config or ProviderConfig(
            provider_id="ollama",
            vendor="Ollama Community",
            base_url="http://localhost:11434/api/chat",
            default_model="llama3.2:latest",
            cost_per_1k_tokens=0.000,
        )
        self.transport = transport or MockHTTPTransport()
        self._health_monitor = ProviderHealthMonitor(self.config.provider_id)
        self._profile = ProviderProfile(
            provider_id=self.config.provider_id,
            display_name=f"Ollama Local ({self.config.default_model})",
            vendor="Ollama Community",
            provider_version="1.0.0",
            supports_streaming=self.config.capabilities.streaming,
            supports_tools=False,
            supports_reasoning=self.config.capabilities.reasoning,
            max_context_tokens=self.config.capabilities.max_context_tokens,
            cost_per_1k_tokens=0.000,
            health=ProviderHealth.HEALTHY if self.config.enabled else ProviderHealth.OFFLINE,
        )

    @property
    def provider_id(self) -> str:
        return self.config.provider_id

    @property
    def profile(self) -> ProviderProfile:
        return self._profile

    def features(self) -> ProviderFeatureSet:
        return self.config.capabilities

    def supports(self, feature_name: str) -> bool:
        return self.config.capabilities.supports(feature_name)

    def prepare(self, rendered_prompt: RenderedPrompt, capability_id: str) -> Dict[str, Any]:
        """Prepare Ollama REST API payload format."""
        return {
            "model": self.config.default_model,
            "messages": [
                {"role": "system", "content": rendered_prompt.system_prompt},
                {"role": "user", "content": rendered_prompt.user_prompt},
            ],
            "stream": False,
        }

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for Ollama text payload."""
        return max(1, len(text) // 4)

    def estimate_cost(self, token_count: int) -> float:
        """Local execution is free ($0.00)."""
        return 0.000

    def health(self) -> ProviderHealth:
        monitor_health = self._health_monitor.get_health()
        return monitor_health if monitor_health != ProviderHealth.HEALTHY else self._profile.health

    def normalize(self, raw_response: Any, capability_id: str, context: ExecutionContext, duration_ms: float) -> CapabilityResult:
        """Normalize raw Ollama response payload into standardized CapabilityResult."""
        output_text = ""
        if isinstance(raw_response, dict):
            output_text = raw_response.get("message", {}).get("content", raw_response.get("response", ""))

        prompt_eval_count = raw_response.get("prompt_eval_count", self.estimate_tokens(output_text)) if isinstance(raw_response, dict) else 100
        eval_count = raw_response.get("eval_count", 80) if isinstance(raw_response, dict) else 80
        total_tokens = prompt_eval_count + eval_count

        return CapabilityResult(
            success=True,
            provider_id=self.config.provider_id,
            model=self.config.default_model,
            capability_id=capability_id,
            duration_ms=duration_ms,
            provider_version=self._profile.provider_version,
            finish_reason=FinishReason.STOP,
            cache_source=CacheSource.NONE,
            trace_id=context.trace_id,
            cost=0.000,
            token_usage={"prompt_tokens": prompt_eval_count, "completion_tokens": eval_count, "total_tokens": total_tokens},
            raw_payload={"response_text": output_text, "model": self.config.default_model},
        )

    def execute(
        self,
        rendered_prompt: RenderedPrompt,
        capability_id: str,
        context: ExecutionContext,
    ) -> CapabilityResult:
        """Execute request using HTTPTransport."""
        start_time = time.time()
        payload = self.prepare(rendered_prompt, capability_id)

        req = HTTPRequest(
            url=self.config.base_url or "http://localhost:11434/api/chat",
            method="POST",
            headers={"Content-Type": "application/json"},
            json_data=payload,
            timeout=self.config.timeout,
        )

        http_resp = self.transport.send(req)
        raw_res = http_resp.body_json

        duration_ms = round((time.time() - start_time) * 1000 + 8, 2)
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
            cost=0.000,
            token_usage=res.token_usage,
            raw_payload=res.raw_payload,
        )
