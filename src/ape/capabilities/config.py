"""
Provider Configuration & Capabilities Specification — ORION-112 / ORION-113.
Defines ProviderFeatureSet, ProviderCapabilities, and ProviderConfig dataclasses.
"""

import os
from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class ProviderFeatureSet:
    """Immutable provider capability feature flags descriptor."""
    streaming: bool = True
    reasoning: bool = True
    vision: bool = False
    tool_calling: bool = True
    json_mode: bool = True
    audio: bool = False
    embeddings: bool = False
    max_context_tokens: int = 128000

    def supports(self, feature_name: str) -> bool:
        """Check if feature flag is supported."""
        return getattr(self, feature_name, False)

    def is_subset(self, required: "ProviderFeatureSet") -> bool:
        """Check if all required features are supported by this feature set."""
        for feat in ["streaming", "reasoning", "vision", "tool_calling", "json_mode", "audio", "embeddings"]:
            if getattr(required, feat, False) and not getattr(self, feat, False):
                return False
        return True


@dataclass(frozen=True)
class ProviderCapabilities:
    """Immutable provider capabilities descriptor."""
    supports_streaming: bool = True
    supports_tools: bool = True
    supports_reasoning: bool = True
    supports_images: bool = False
    supports_audio: bool = False
    supports_embeddings: bool = False
    supports_json_mode: bool = True
    max_context_tokens: int = 128000


@dataclass
class ProviderConfig:
    """Provider configuration model decoupling environment variable resolution from adapters."""
    provider_id: str
    vendor: str = ""
    base_url: str = ""
    api_key_env: str = ""
    default_model: str = ""
    timeout: float = 60.0
    max_retries: int = 3
    enabled: bool = True
    cost_per_1k_tokens: float = 0.002
    headers: Dict[str, str] = field(default_factory=dict)
    capabilities: ProviderFeatureSet = field(default_factory=ProviderFeatureSet)

    @property
    def api_key(self) -> str:
        if self.api_key_env:
            return os.getenv(self.api_key_env, "")
        return ""
