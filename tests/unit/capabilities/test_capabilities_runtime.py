"""
Unit tests for ORION-113 Execution Runtime Platform.
Verifies ProviderFeatureSet matching, RuntimeContext state tracking, ProviderEndpointKey CircuitBreaker state transitions,
strategy-based RetryOrchestrator, platform EventBus broadcasting, MetricsCollector aggregation, and HealthMonitor status derivation.
"""

import time

import pytest

from ape.capabilities import (
    CapabilityBroker,
    CapabilityMatrix,
    CapabilityRegistry,
    CircuitBreakerOpenError,
    CircuitBreakerState,
    EventBus,
    ExecutionContext,
    ExecutionPolicy,
    HealthMonitor,
    ImmediateRetryStrategy,
    MetricsCollector,
    MockProviderAdapter,
    ProviderCircuitBreaker,
    ProviderEndpointKey,
    ProviderFeatureSet,
    ProviderHealth,
    ProviderRegistry,
    ProviderRetryOrchestrator,
    RuntimeContext,
    RuntimeEvent,
)
from ape.prompts import RenderedPrompt


@pytest.fixture
def sample_rendered_prompt() -> RenderedPrompt:
    return RenderedPrompt(
        system_prompt="You are an AI Operating System kernel.",
        user_prompt="Run execution runtime tests.",
        prompt_id="engineering.nextjs_blueprint",
        version="1.0.0",
        template_sha256="sha_tmpl_113",
        rendered_sha256="sha_rnd_113",
        trace_id="trc_runtime_113",
    )


@pytest.fixture
def sample_context() -> ExecutionContext:
    return ExecutionContext(
        execution_id="ex_runtime_113",
        venture_id="v_runtime_113",
        trace_id="trc_runtime_113",
        workspace_id="ws_runtime_113",
    )


def test_provider_feature_set_matching():
    feats_smart = ProviderFeatureSet(streaming=True, reasoning=True, vision=True, tool_calling=True)
    feats_basic = ProviderFeatureSet(streaming=True, reasoning=False, vision=False, tool_calling=False)

    req = ProviderFeatureSet(reasoning=True, vision=True)
    assert feats_smart.is_subset(req) is True
    assert feats_basic.is_subset(req) is False


def test_runtime_context_state_tracking():
    ctx = RuntimeContext(
        execution_id="ex_test",
        trace_id="trc_test",
        selected_provider_id="claude",
        selected_model="claude-3-5-sonnet",
        circuit_state="CLOSED",
    )
    time.sleep(0.01)
    assert ctx.attempt == 1
    assert ctx.elapsed_ms > 0.0
    assert ctx.selected_provider_id == "claude"


def test_provider_endpoint_key_circuit_breaker():
    key_sonnet = ProviderEndpointKey("claude", "claude-3-5-sonnet")
    key_haiku = ProviderEndpointKey("claude", "claude-3-haiku")

    cb = ProviderCircuitBreaker(failure_threshold=2, recovery_timeout_s=0.1)

    # Initial state CLOSED
    assert cb.get_state(key_sonnet) == CircuitBreakerState.CLOSED
    assert cb.get_state(key_haiku) == CircuitBreakerState.CLOSED

    # Record 2 failures on Sonnet
    cb.record_failure(key_sonnet)
    assert cb.get_state(key_sonnet) == CircuitBreakerState.CLOSED
    cb.record_failure(key_sonnet)
    assert cb.get_state(key_sonnet) == CircuitBreakerState.OPEN

    # Haiku remains CLOSED
    assert cb.get_state(key_haiku) == CircuitBreakerState.CLOSED

    # Execution rejection test on Sonnet
    with pytest.raises(CircuitBreakerOpenError):
        cb.check_execution_allowed(key_sonnet)

    # Recovery timeout test
    time.sleep(0.15)
    assert cb.get_state(key_sonnet) == CircuitBreakerState.HALF_OPEN

    # Successful call resets Sonnet to CLOSED
    cb.record_success(key_sonnet)
    assert cb.get_state(key_sonnet) == CircuitBreakerState.CLOSED


def test_strategy_based_retry_orchestrator():
    orchestrator = ProviderRetryOrchestrator()
    calls = []

    def failing_func():
        calls.append(len(calls) + 1)
        if len(calls) < 3:
            raise ValueError("Transient error")
        return "SUCCESS"

    res = orchestrator.execute_with_retry(
        failing_func,
        max_retries=3,
        strategy=ImmediateRetryStrategy(),
    )

    assert res == "SUCCESS"
    assert len(calls) == 3


def test_event_bus_metrics_collector_and_health_monitor():
    bus = EventBus()
    collector = MetricsCollector(bus)
    monitor = HealthMonitor(collector, failure_threshold=2)

    events_received = []
    bus.subscribe(lambda e: events_received.append(e))

    # Publish events
    bus.publish(RuntimeEvent("ExecutionStarted", "cap1", "trc1", provider_id="p1"))
    bus.publish(RuntimeEvent("ExecutionCompleted", "cap1", "trc1", provider_id="p1", details={"cost": 0.005, "duration_ms": 45.0}))

    assert len(events_received) == 2
    metrics = collector.get_metrics("p1")
    assert metrics["successful_calls"] == 1
    assert metrics["total_cost"] == 0.005
    assert monitor.get_health("p1") == ProviderHealth.HEALTHY

    # Simulate failures
    bus.publish(RuntimeEvent("ExecutionFailed", "cap1", "trc1", provider_id="p1"))
    bus.publish(RuntimeEvent("ExecutionFailed", "cap1", "trc1", provider_id="p1"))
    assert monitor.get_health("p1") == ProviderHealth.OFFLINE


def test_capability_broker_feature_filtering_and_event_bus(sample_rendered_prompt, sample_context):
    cap_reg = CapabilityRegistry()
    prov_reg = ProviderRegistry()

    p_smart = MockProviderAdapter(
        provider_id="smart-llm",
        features=ProviderFeatureSet(reasoning=True, vision=True),
    )
    p_basic = MockProviderAdapter(
        provider_id="basic-llm",
        features=ProviderFeatureSet(reasoning=False, vision=False),
    )
    prov_reg.register(p_smart)
    prov_reg.register(p_basic)

    matrix = CapabilityMatrix(prov_reg)
    matrix.map_capability("engineering.code.generate", ["smart-llm", "basic-llm"])

    broker = CapabilityBroker(cap_reg, prov_reg, matrix)
    published_events = []
    broker.add_event_hook(lambda e: published_events.append(e))

    # Execute request requiring vision feature
    policy = ExecutionPolicy(required_features=["vision"])
    res = broker.execute("engineering.code.generate", sample_rendered_prompt, sample_context, policy=policy)

    assert res.provider_id == "smart-llm"
    event_types = [e.event_type for e in published_events]
    assert "CapabilityRequested" in event_types
    assert "ProviderSelected" in event_types
    assert "ExecutionStarted" in event_types
    assert "ExecutionCompleted" in event_types
