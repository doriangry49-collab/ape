"""
Anthropic Claude ProviderAdapter — ORION-112 Specification.
Thin integration adapter for Anthropic Claude models using ProviderConfig and HTTPTransport abstraction.
"""

import time
from typing import Any, Dict, Optional

from ape.capabilities.adapters_base import (
    ProviderFeatureSet,
    ProviderHealth,
    ProviderHealthMonitor,
    ProviderProfile,
)
from ape.capabilities.config import ProviderConfig
from ape.capabilities.contracts import CacheSource, CapabilityResult, ExecutionContext, FinishReason
from ape.capabilities.transport import HTTPRequest, HTTPTransport, MockHTTPTransport
from ape.prompts.template import RenderedPrompt


class ClaudeProviderAdapter:
    """Thin Anthropic Claude ProviderAdapter implementing full ProviderAdapter lifecycle contract."""

    def __init__(
        self,
        config: Optional[ProviderConfig] = None,
        transport: Optional[HTTPTransport] = None,
    ) -> None:
        self.config = config or ProviderConfig(
            provider_id="claude",
            vendor="Anthropic",
            base_url="https://api.anthropic.com/v1/messages",
            api_key_env="ANTHROPIC_API_KEY",
            default_model="claude-3-5-sonnet-20241022",
            cost_per_1k_tokens=0.003,
        )
        self.transport = transport or MockHTTPTransport()
        self._health_monitor = ProviderHealthMonitor(self.config.provider_id)
        self._profile = ProviderProfile(
            provider_id=self.config.provider_id,
            display_name=f"Anthropic Claude ({self.config.default_model})",
            vendor="Anthropic",
            provider_version="1.0.0",
            supports_streaming=self.config.capabilities.streaming,
            supports_tools=self.config.capabilities.tool_calling,
            supports_reasoning=self.config.capabilities.reasoning,
            max_context_tokens=self.config.capabilities.max_context_tokens,
            cost_per_1k_tokens=0.003,
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
        """Prepare Anthropic API payload format."""
        return {
            "model": self.config.default_model,
            "system": rendered_prompt.system_prompt,
            "messages": [
                {"role": "user", "content": rendered_prompt.user_prompt}
            ],
            "max_tokens": 4096,
        }

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for Anthropic Claude text payload."""
        return max(1, len(text) // 4)

    def estimate_cost(self, token_count: int) -> float:
        """Estimate execution cost for token count."""
        return round((token_count / 1000.0) * 0.003, 6)

    def health(self) -> ProviderHealth:
        monitor_health = self._health_monitor.get_health()
        return monitor_health if monitor_health != ProviderHealth.HEALTHY else self._profile.health

    def normalize(self, raw_response: Any, capability_id: str, context: ExecutionContext, duration_ms: float) -> CapabilityResult:
        """Normalize raw Anthropic response payload into standardized CapabilityResult."""
        output_text = raw_response.get("content", [{}])[0].get("text", "") if isinstance(raw_response, dict) else str(raw_response)
        stop_reason = raw_response.get("stop_reason", "end_turn") if isinstance(raw_response, dict) else "end_turn"

        finish_reason = FinishReason.STOP
        if stop_reason == "max_tokens":
            finish_reason = FinishReason.MAX_TOKENS

        usage_raw = raw_response.get("usage", {}) if isinstance(raw_response, dict) else {}
        input_tokens = usage_raw.get("input_tokens", self.estimate_tokens(output_text))
        output_tokens = usage_raw.get("output_tokens", 100)
        total_tokens = input_tokens + output_tokens
        cost = self.estimate_cost(total_tokens)

        return CapabilityResult(
            success=True,
            provider_id=self.config.provider_id,
            model=self.config.default_model,
            capability_id=capability_id,
            duration_ms=duration_ms,
            provider_version=self._profile.provider_version,
            finish_reason=finish_reason,
            cache_source=CacheSource.NONE,
            trace_id=context.trace_id,
            cost=cost,
            token_usage={"prompt_tokens": input_tokens, "completion_tokens": output_tokens, "total_tokens": total_tokens},
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
            url=self.config.base_url or "https://api.anthropic.com/v1/messages",
            method="POST",
            headers={"x-api-key": self.config.api_key, "anthropic-version": "2023-06-01"},
            json_data=payload,
            timeout=self.config.timeout,
        )

        http_resp = self.transport.send(req)
        raw_res = http_resp.body_json

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
