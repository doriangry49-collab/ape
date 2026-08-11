"""
Shared Contract Unit Tests for ORION-112 Real Provider Adapters (Claude, Gemini, OpenAI, Ollama).
Verifies ProviderConfig, ProviderCapabilities, plugin-based ProviderFactory, MockHTTPTransport,
and shared ProviderAdapterContractTests lifecycle compliance across all 4 production provider adapters.
"""

import pytest

from ape.capabilities import (
    CacheSource,
    CapabilityResult,
    ClaudeProviderAdapter,
    ExecutionContext,
    FinishReason,
    GeminiProviderAdapter,
    MockHTTPTransport,
    OllamaProviderAdapter,
    OpenAIProviderAdapter,
    ProviderAdapter,
    ProviderCapabilities,
    ProviderConfig,
    ProviderFactory,
    ProviderHealth,
)
from ape.prompts import RenderedPrompt


@pytest.fixture
def sample_prompt() -> RenderedPrompt:
    return RenderedPrompt(
        system_prompt="You are an expert software architect.",
        user_prompt="Generate Next.js 14 blueprint scaffold.",
        prompt_id="engineering.nextjs_blueprint",
        version="1.0.0",
        template_sha256="sha_tmpl_001",
        rendered_sha256="sha_rnd_002",
        trace_id="trc_shared_contract",
    )


@pytest.fixture
def sample_context() -> ExecutionContext:
    return ExecutionContext(
        execution_id="ex_shared_contract",
        venture_id="v_contract_01",
        trace_id="trc_shared_contract",
        workspace_id="ws_contract_01",
    )


class ProviderAdapterContractTests:
    """Shared base contract test suite inherited by all provider adapter test cases."""

    def assert_adapter_lifecycle_compliance(self, adapter: ProviderAdapter, sample_prompt: RenderedPrompt, sample_context: ExecutionContext):
        # 1. Identity & Health Check
        assert isinstance(adapter, ProviderAdapter)
        assert adapter.provider_id != ""
        assert adapter.health() == ProviderHealth.HEALTHY

        # 2. Prepare Payload
        prepared = adapter.prepare(sample_prompt, "engineering.code.generate")
        assert isinstance(prepared, dict)

        # 3. Token & Cost Estimation
        tokens = adapter.estimate_tokens(sample_prompt.user_prompt)
        assert tokens > 0
        cost = adapter.estimate_cost(1000)
        assert cost >= 0.0

        # 4. Execute & Normalize Contract Check
        res = adapter.execute(sample_prompt, "engineering.code.generate", sample_context)
        assert isinstance(res, CapabilityResult)
        assert res.success is True
        assert res.provider_id == adapter.provider_id
        assert isinstance(res.finish_reason, FinishReason)
        assert isinstance(res.cache_source, CacheSource)
        assert res.token_usage["total_tokens"] > 0


def test_provider_config_and_capabilities_descriptor():
    caps = ProviderCapabilities(supports_streaming=True, supports_reasoning=True, max_context_tokens=200000)
    cfg = ProviderConfig(
        provider_id="claude-enterprise",
        vendor="Anthropic",
        base_url="https://api.anthropic.com/v1/messages",
        api_key_env="ANTHROPIC_API_KEY",
        default_model="claude-3-5-sonnet",
        capabilities=caps,
        enabled=True,
    )

    assert cfg.provider_id == "claude-enterprise"
    assert cfg.capabilities.max_context_tokens == 200000
    assert cfg.enabled is True


def test_provider_factory_plugin_creation():
    factory = ProviderFactory()
    cfg = ProviderConfig(provider_id="ollama", default_model="llama3.2")
    transport = MockHTTPTransport()

    adapter = factory.create(cfg, transport)
    assert adapter.provider_id == "ollama"
    assert adapter.profile.vendor == "Ollama Community"


def test_claude_adapter_contract(sample_prompt, sample_context):
    adapter = ClaudeProviderAdapter()
    tester = ProviderAdapterContractTests()
    tester.assert_adapter_lifecycle_compliance(adapter, sample_prompt, sample_context)


def test_gemini_adapter_contract(sample_prompt, sample_context):
    adapter = GeminiProviderAdapter()
    tester = ProviderAdapterContractTests()
    tester.assert_adapter_lifecycle_compliance(adapter, sample_prompt, sample_context)


def test_openai_adapter_contract(sample_prompt, sample_context):
    adapter = OpenAIProviderAdapter()
    tester = ProviderAdapterContractTests()
    tester.assert_adapter_lifecycle_compliance(adapter, sample_prompt, sample_context)


def test_ollama_adapter_contract(sample_prompt, sample_context):
    adapter = OllamaProviderAdapter()
    tester = ProviderAdapterContractTests()
    tester.assert_adapter_lifecycle_compliance(adapter, sample_prompt, sample_context)
    assert adapter.estimate_cost(10000) == 0.000  # Zero local cost
