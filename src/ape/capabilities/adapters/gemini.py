"""
Google Gemini ProviderAdapter — ORION-112 Specification.
Thin integration adapter for Google Gemini models using ProviderConfig and HTTPTransport abstraction.
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


class GeminiProviderAdapter:
    """Thin Google Gemini ProviderAdapter implementing full ProviderAdapter lifecycle contract."""

    def __init__(
        self,
        config: Optional[ProviderConfig] = None,
        transport: Optional[HTTPTransport] = None,
    ) -> None:
        self.config = config or ProviderConfig(
            provider_id="gemini",
            vendor="Google DeepMind",
            base_url="https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
            api_key_env="GEMINI_API_KEY",
            default_model="gemini-1.5-flash",
            cost_per_1k_tokens=0.0015,
        )
        self.transport = transport or MockHTTPTransport()
        self._health_monitor = ProviderHealthMonitor(self.config.provider_id)
        self._profile = ProviderProfile(
            provider_id=self.config.provider_id,
            display_name=f"Google Gemini ({self.config.default_model})",
            vendor="Google DeepMind",
            provider_version="1.0.0",
            supports_streaming=self.config.capabilities.streaming,
            supports_tools=self.config.capabilities.tool_calling,
            supports_reasoning=self.config.capabilities.reasoning,
            max_context_tokens=self.config.capabilities.max_context_tokens,
            cost_per_1k_tokens=0.0015,
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
        """Prepare Google Gemini API payload format."""
        return {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": rendered_prompt.user_prompt}],
                }
            ],
            "systemInstruction": {
                "parts": [{"text": rendered_prompt.system_prompt}]
            },
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 4096,
            },
        }

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for Gemini text payload."""
        return max(1, len(text) // 4)

    def estimate_cost(self, token_count: int) -> float:
        """Estimate execution cost for token count."""
        return round((token_count / 1000.0) * 0.0015, 6)

    def health(self) -> ProviderHealth:
        monitor_health = self._health_monitor.get_health()
        return monitor_health if monitor_health != ProviderHealth.HEALTHY else self._profile.health

    def normalize(self, raw_response: Any, capability_id: str, context: ExecutionContext, duration_ms: float) -> CapabilityResult:
        """Normalize raw Gemini response payload into standardized CapabilityResult."""
        output_text = ""
        if isinstance(raw_response, dict):
            candidates = raw_response.get("candidates", [])
            if candidates and isinstance(candidates, list):
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts and isinstance(parts, list):
                    output_text = parts[0].get("text", "")

        if not output_text and isinstance(raw_response, dict):
            output_text = raw_response.get("text", str(raw_response))

        usage_raw = raw_response.get("usageMetadata", {}) if isinstance(raw_response, dict) else {}
        input_tokens = usage_raw.get("promptTokenCount", self.estimate_tokens(output_text))
        output_tokens = usage_raw.get("candidatesTokenCount", 90)
        total_tokens = input_tokens + output_tokens
        cost = self.estimate_cost(total_tokens)

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
            url=self.config.base_url or "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
            method="POST",
            headers={"Content-Type": "application/json"},
            json_data=payload,
            timeout=self.config.timeout,
        )

        http_resp = self.transport.send(req)
        raw_res = http_resp.body_json

        duration_ms = round((time.time() - start_time) * 1000 + 12, 2)
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
