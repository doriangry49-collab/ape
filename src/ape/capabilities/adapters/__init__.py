"""
APE Concrete Provider Adapters Subsystem — ORION-112 Specification.
"""

from ape.capabilities.adapters.claude import ClaudeProviderAdapter
from ape.capabilities.adapters.gemini import GeminiProviderAdapter
from ape.capabilities.adapters.ollama import OllamaProviderAdapter
from ape.capabilities.adapters.openai import OpenAIProviderAdapter

__all__ = [
    "ClaudeProviderAdapter",
    "GeminiProviderAdapter",
    "OpenAIProviderAdapter",
    "OllamaProviderAdapter",
]
