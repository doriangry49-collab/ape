"""
Plugin-Based ProviderFactory — ORION-112 Specification.
Decouples adapter instantiation from ProviderRegistry following Open/Closed Principle.
"""

from typing import Callable, Dict, Optional

from ape.capabilities.adapters_base import ProviderAdapter
from ape.capabilities.config import ProviderConfig
from ape.capabilities.contracts import ProviderUnavailableError
from ape.capabilities.transport import HTTPTransport, MockHTTPTransport


class ProviderFactory:
    """Plugin-based ProviderFactory mapping provider_ids to adapter creator functions."""

    def __init__(self) -> None:
        self._creators: Dict[str, Callable[[ProviderConfig, Optional[HTTPTransport]], ProviderAdapter]] = {}
        self._register_default_creators()

    def register_creator(
        self,
        provider_id: str,
        creator_fn: Callable[[ProviderConfig, Optional[HTTPTransport]], ProviderAdapter],
    ) -> None:
        """Register a creator function for a provider_id."""
        self._creators[provider_id] = creator_fn

    def _register_default_creators(self) -> None:
        """Register default adapter creators for built-in providers."""
        def create_claude(cfg: ProviderConfig, transport: Optional[HTTPTransport] = None) -> ProviderAdapter:
            from ape.capabilities.adapters.claude import ClaudeProviderAdapter
            return ClaudeProviderAdapter(config=cfg, transport=transport)

        def create_gemini(cfg: ProviderConfig, transport: Optional[HTTPTransport] = None) -> ProviderAdapter:
            from ape.capabilities.adapters.gemini import GeminiProviderAdapter
            return GeminiProviderAdapter(config=cfg, transport=transport)

        def create_openai(cfg: ProviderConfig, transport: Optional[HTTPTransport] = None) -> ProviderAdapter:
            from ape.capabilities.adapters.openai import OpenAIProviderAdapter
            return OpenAIProviderAdapter(config=cfg, transport=transport)

        def create_ollama(cfg: ProviderConfig, transport: Optional[HTTPTransport] = None) -> ProviderAdapter:
            from ape.capabilities.adapters.ollama import OllamaProviderAdapter
            return OllamaProviderAdapter(config=cfg, transport=transport)

        def create_mock(cfg: ProviderConfig, transport: Optional[HTTPTransport] = None) -> ProviderAdapter:
            from ape.capabilities.adapters_base import MockProviderAdapter
            return MockProviderAdapter(provider_id=cfg.provider_id)

        self._creators["claude"] = create_claude
        self._creators["gemini"] = create_gemini
        self._creators["openai"] = create_openai
        self._creators["ollama"] = create_ollama
        self._creators["mock"] = create_mock

    def create(self, config: ProviderConfig, transport: Optional[HTTPTransport] = None) -> ProviderAdapter:
        """Create a ProviderAdapter instance for the given ProviderConfig."""
        if not config.enabled:
            raise ProviderUnavailableError(f"Provider '{config.provider_id}' is disabled in ProviderConfig.")

        p_id = config.provider_id.lower()
        if p_id not in self._creators:
            raise ProviderUnavailableError(f"No creator function registered for provider '{config.provider_id}' in ProviderFactory.")

        creator_fn = self._creators[p_id]
        transport = transport or MockHTTPTransport()
        return creator_fn(config, transport)
