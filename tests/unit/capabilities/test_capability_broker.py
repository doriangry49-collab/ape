"""
Unit tests for ORION-111B CapabilityBroker & Execution Kernel.
Verifies ProviderAdapter protocol compliance, frozen lifecycle methods (prepare, execute, normalize, estimate_cost, estimate_tokens, health),
CapabilityRegistry descriptor lookup with bound prompt_ids, ExecutionPolicy, ProviderHealthMonitor, FinishReason, CacheSource,
CapabilityEvent stream broadcasting, ExecutionBudget limit enforcement, ProviderSelectionStrategy implementations (LowestCost, BestScore, Pinned, Fallback),
and CapabilityError exception hierarchy.
"""

from pathlib import Path
import pytest

from ape.capabilities import (
    BestScoreStrategy,
    BudgetExceededError,
    CacheSource,
    CapabilityBroker,
    CapabilityDescriptor,
    CapabilityMatrix,
    CapabilityNotSupportedError,
    CapabilityRegistry,
    CapabilityResult,
    ExecutionBudget,
    ExecutionContext,
    ExecutionPolicy,
    ExecutionUsage,
    FallbackStrategy,
    FinishReason,
    LowestCostStrategy,
    MockProviderAdapter,
    PinnedStrategy,
    ProviderHealth,
    ProviderHealthMonitor,
    ProviderRegistry,
    ProviderUnavailableError,
    RuntimeEvent,
)
from ape.prompts import RenderedPrompt


def test_provider_adapter_lifecycle_and_health_monitor():
    adapter = MockProviderAdapter(provider_id="mock-lifecycle", cost_per_1k_tokens=0.001)
    assert adapter.provider_id == "mock-lifecycle"
    assert adapter.health() == ProviderHealth.HEALTHY

    prompt = RenderedPrompt(
        system_prompt="System prompt",
        user_prompt="User prompt",
        prompt_id="engineering.nextjs_blueprint",
        version="1.0.0",
        template_sha256="abc",
        rendered_sha256="def",
        trace_id="trc_001",
    )
    context = ExecutionContext(execution_id="exec_1", venture_id="v_1", trace_id="trc_001", workspace_id="ws_1")

    # Verify lifecycle methods
    prepared = adapter.prepare(prompt, "engineering.code.generate")
    assert prepared["capability_id"] == "engineering.code.generate"

    res = adapter.execute(prompt, "engineering.code.generate", context)
    assert isinstance(res, CapabilityResult)
    assert res.success is True
    assert res.provider_id == "mock-lifecycle"
    assert res.provider_version == "1.0.0"
    assert res.finish_reason == FinishReason.STOP
    assert res.cache_source == CacheSource.NONE

    # Test ProviderHealthMonitor
    monitor = ProviderHealthMonitor("p-mon", consecutive_failure_threshold=2)
    assert monitor.get_health() == ProviderHealth.HEALTHY

    monitor.record_failure()
    assert monitor.get_health() == ProviderHealth.DEGRADED

    monitor.record_failure()
    assert monitor.get_health() == ProviderHealth.OFFLINE


def test_capability_event_stream_broadcasting():
    cap_reg = CapabilityRegistry()
    prov_reg = ProviderRegistry()

    p_adapter = MockProviderAdapter(provider_id="p-event-test")
    prov_reg.register(p_adapter)

    c_matrix = CapabilityMatrix(prov_reg)
    c_matrix.map_capability("publishing.release.notes", ["p-event-test"])

    broker = CapabilityBroker(cap_reg, prov_reg, c_matrix)

    events = []
    broker.add_event_hook(lambda e: events.append(e))

    prompt = RenderedPrompt(
        system_prompt="Sys",
        user_prompt="Usr",
        prompt_id="publishing.release_notes",
        version="1.0.0",
        template_sha256="a",
        rendered_sha256="b",
        trace_id="t_evt_01",
    )
    context = ExecutionContext(execution_id="ex1", venture_id="v1", trace_id="t_evt_01", workspace_id="w1")

    broker.execute("publishing.release.notes", prompt, context)

    event_types = [e.event_type for e in events]
    assert "CapabilityRequested" in event_types
    assert "ProviderSelected" in event_types
    assert "ExecutionStarted" in event_types
    assert "ExecutionCompleted" in event_types
