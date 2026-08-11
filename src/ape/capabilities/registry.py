"""
Capability & Provider Registries + Multi-Dimensional ProviderScore — ORION-111B / ORION-112 / ORION-114.
Provides decoupled CapabilityRegistry, ProviderRegistry, and CapabilityMatrix with multi-dimensional ProviderScore.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from ape.capabilities.adapters_base import ProviderAdapter, ProviderHealth
from ape.capabilities.contracts import CapabilityNotSupportedError, ProviderUnavailableError


@dataclass(frozen=True)
class CapabilityDescriptor:
    """Immutable capability metadata descriptor binding canonical capability_ids to default prompt_ids."""
    capability_id: str
    category: str
    description: str
    prompt_id: str = ""
    default_strategy: str = "LOWEST_COST"
    budget_profile: str = "standard"
    allowed_providers: List[str] = field(default_factory=list)
    input_schema: Dict[str, str] = field(default_factory=dict)
    output_schema: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderScore:
    """Multi-dimensional provider score rating across quality, availability, latency, cost, and freshness."""
    provider_id: str
    quality: float = 95.0
    availability: float = 99.9
    latency_ms: float = 50.0
    cost: float = 0.002
    confidence: float = 90.0
    freshness: float = 100.0

    @property
    def score(self) -> float:
        """Calculate composite quality rating (0 to 100)."""
        latency_penalty = max(0.0, (self.latency_ms - 20.0) / 10.0)
        cost_penalty = self.cost * 1000.0
        avail_penalty = max(0.0, (100.0 - self.availability) * 5.0)

        composite = (self.quality * 0.4) + (self.confidence * 0.3) + (self.freshness * 0.3) - latency_penalty - cost_penalty - avail_penalty
        return max(0.0, round(composite, 2))


class CapabilityRegistry:
    """Central registry storing canonical capability definitions with bound prompt_ids."""

    def __init__(self) -> None:
        self._capabilities: Dict[str, CapabilityDescriptor] = {}
        self._populate_defaults()

    def _populate_defaults(self) -> None:
        defaults = [
            CapabilityDescriptor(
                capability_id="research.market.analysis",
                category="research",
                description="Performs competitive market analysis and target customer profiling.",
                prompt_id="research.market_analysis",
            ),
            CapabilityDescriptor(
                capability_id="engineering.code.generate",
                category="engineering",
                description="Generates software architecture scaffolds, code modules, and configs.",
                prompt_id="engineering.nextjs_blueprint",
            ),
            CapabilityDescriptor(
                capability_id="marketing.copy.generate",
                category="marketing",
                description="Generates marketing landing page copy, value props, and SEO content.",
                prompt_id="marketing.landing_page",
            ),
            CapabilityDescriptor(
                capability_id="publishing.release.notes",
                category="publishing",
                description="Generates deployment proof and release notes for venture publishing.",
                prompt_id="publishing.release_notes",
            ),
        ]
        for cap in defaults:
            self._capabilities[cap.capability_id] = cap

    def register(self, descriptor: CapabilityDescriptor) -> None:
        self._capabilities[descriptor.capability_id] = descriptor

    def get(self, capability_id: str) -> CapabilityDescriptor:
        if capability_id not in self._capabilities:
            raise CapabilityNotSupportedError(f"Capability '{capability_id}' is not registered in CapabilityRegistry.")
        return self._capabilities[capability_id]

    def has(self, capability_id: str) -> bool:
        return capability_id in self._capabilities


class ProviderRegistry:
    """Registry storing registered ProviderAdapters."""

    def __init__(self) -> None:
        self._adapters: Dict[str, ProviderAdapter] = {}
        self._populate_defaults()

    def _populate_defaults(self) -> None:
        """Lazy-load and register built-in provider adapters."""
        try:
            from ape.capabilities.adapters.claude import ClaudeProviderAdapter
            from ape.capabilities.adapters.gemini import GeminiProviderAdapter
            from ape.capabilities.adapters.ollama import OllamaProviderAdapter
            from ape.capabilities.adapters.openai import OpenAIProviderAdapter
            from ape.capabilities.adapters_base import MockProviderAdapter

            self.register(MockProviderAdapter())
            self.register(ClaudeProviderAdapter())
            self.register(GeminiProviderAdapter())
            self.register(OpenAIProviderAdapter())
            self.register(OllamaProviderAdapter())
        except Exception:
            pass

    def register(self, adapter: ProviderAdapter) -> None:
        self._adapters[adapter.provider_id] = adapter

    def get(self, provider_id: str) -> ProviderAdapter:
        if provider_id not in self._adapters:
            raise ProviderUnavailableError(f"Provider adapter '{provider_id}' is not registered in ProviderRegistry.")
        return self._adapters[provider_id]

    def has(self, provider_id: str) -> bool:
        return provider_id in self._adapters

    def list_adapters(self) -> List[ProviderAdapter]:
        return list(self._adapters.values())


class CapabilityMatrix:
    """Maps capability_ids to supporting ProviderAdapters filtered by ProviderHealth."""

    def __init__(self, provider_registry: ProviderRegistry) -> None:
        self.provider_registry = provider_registry
        self._matrix: Dict[str, List[str]] = {}

    def map_capability(self, capability_id: str, provider_ids: List[str]) -> None:
        self._matrix[capability_id] = provider_ids

    def get_candidate_adapters(self, capability_id: str) -> List[ProviderAdapter]:
        """Return healthy candidate ProviderAdapters for requested capability_id."""
        if capability_id not in self._matrix:
            all_adapters = self.provider_registry.list_adapters()
            healthy = [a for a in all_adapters if a.profile.health == ProviderHealth.HEALTHY]
            if not healthy:
                raise ProviderUnavailableError(f"No healthy provider adapters available for capability '{capability_id}'.")
            return healthy

        provider_ids = self._matrix[capability_id]
        candidates = []
        for p_id in provider_ids:
            if self.provider_registry.has(p_id):
                adapter = self.provider_registry.get(p_id)
                if adapter.profile.health == ProviderHealth.HEALTHY:
                    candidates.append(adapter)

        if not candidates:
            raise ProviderUnavailableError(f"No healthy provider adapters available for capability '{capability_id}'.")

        return candidates
