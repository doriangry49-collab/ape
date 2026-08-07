"""
Model-Agnostic LLM Provider Adapters — ORION-109A Specification.
Defines LLMProviderProtocol contract and deterministic MockLLMProvider for offline unit tests.
"""

from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class LLMProviderProtocol(Protocol):
    """Abstract protocol for model-agnostic LLM provider completions."""

    def complete(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text completion for prompt."""
        ...


class MockLLMProvider:
    """Deterministic offline mock LLM provider for fast unit testing."""

    def __init__(self, default_response: str = "") -> None:
        self.default_response = default_response or "Mock LLM completion payload for prompt."

    def complete(self, prompt: str, system_prompt: str = "") -> str:
        """Return deterministic completion."""
        return f"[MockLLM] {self.default_response} (Prompt: '{prompt[:30]}...')"
