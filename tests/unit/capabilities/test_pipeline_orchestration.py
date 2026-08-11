"""
Unit tests for ORION-114 Execution Pipeline & Orchestration Engine.
Verifies pluggable ExecutionStage lifecycle (before, execute, after, rollback), functional ExecutionState,
unified ExecutionResult (final, stream, trace), event-sourced ExecutionTrace, ExecutionArtifact models,
multi-dimensional ProviderScore, and modular Selection Strategies.
"""

import pytest

from ape.capabilities import (
    ArtifactType,
    BaseExecutionStage,
    CapabilityBroker,
    CapabilityMatrix,
    CapabilityRegistry,
    ExecutionContext,
    ExecutionEngine,
    ExecutionResult,
    ExecutionState,
    ExecutionTrace,
    HighestQualityStrategy,
    LocalOnlyStrategy,
    LowestCostStrategy,
    MockProviderAdapter,
    ProviderFeatureSet,
    ProviderRegistry,
    ProviderScore,
    RuntimeContext,
    RuntimeEvent,
    ToolCall,
    ToolDefinition,
)
from ape.capabilities.artifacts import ExecutionArtifact
from ape.prompts import RenderedPrompt


@pytest.fixture
def sample_prompt() -> RenderedPrompt:
    return RenderedPrompt(
        system_prompt="You are an AI Operating System Kernel.",
        user_prompt="Run pipeline orchestration tests.",
        prompt_id="engineering.nextjs_blueprint",
        version="1.0.0",
        template_sha256="sha_tmpl_114",
        rendered_sha256="sha_rnd_114",
        trace_id="trc_pipeline_114",
    )


@pytest.fixture
def sample_context() -> ExecutionContext:
    return ExecutionContext(
        execution_id="ex_pipe_114",
        venture_id="v_pipe_114",
        trace_id="trc_pipeline_114",
        workspace_id="ws_pipe_114",
    )


def test_execution_stage_lifecycle_and_engine(sample_prompt, sample_context):
    class CustomCustomStage(BaseExecutionStage):
        stage_name = "CustomCustomStage"
        executed = False

        def execute(self, state: ExecutionState) -> ExecutionState:
            self.executed = True
            state.working_memory["custom_stage_run"] = True
            return state

    engine = ExecutionEngine()
    custom_stage = CustomCustomStage()
    engine.add_stage(custom_stage)

    runtime_ctx = RuntimeContext(execution_id=sample_context.execution_id, trace_id=sample_context.trace_id)
    state = ExecutionState(
        context=sample_context,
        runtime=runtime_ctx,
        capability_id="engineering.code.generate",
        rendered_prompt=sample_prompt,
    )

    engine.execute_pipeline(state)
    assert custom_stage.executed is True
    assert state.working_memory.get("custom_stage_run") is True


def test_unified_execution_result(sample_prompt, sample_context):
    cap_reg = CapabilityRegistry()
    prov_reg = ProviderRegistry()

    p_mock = MockProviderAdapter("mock-p1")
    prov_reg.register(p_mock)

    matrix = CapabilityMatrix(prov_reg)
    matrix.map_capability("engineering.code.generate", ["mock-p1"])

    broker = CapabilityBroker(cap_reg, prov_reg, matrix)
    exec_res = broker.execute_pipeline("engineering.code.generate", sample_prompt, sample_context)

    assert isinstance(exec_res, ExecutionResult)
    final_res = exec_res.final()
    assert final_res.success is True
    assert final_res.provider_id == "mock-p1"

    trace = exec_res.trace()
    assert isinstance(trace, ExecutionTrace)
    assert trace.trace_id == sample_context.trace_id

    stream_list = list(exec_res.stream())
    assert isinstance(stream_list, list)


def test_event_sourced_execution_trace():
    events = [
        RuntimeEvent("CapabilityRequested", "cap1", "trc1"),
        RuntimeEvent("ProviderSelected", "cap1", "trc1", provider_id="claude"),
        RuntimeEvent("ExecutionCompleted", "cap1", "trc1", provider_id="claude"),
    ]
    trace = ExecutionTrace(trace_id="trc1", capability_id="cap1", execution_id="ex1", events=events, duration_ms=45.2)

    summary = trace.summary()
    assert summary["trace_id"] == "trc1"
    assert summary["selected_provider"] == "claude"
    assert summary["total_events"] == 3


def test_execution_artifact_multimodal():
    art = ExecutionArtifact(
        artifact_id="art_001",
        artifact_type=ArtifactType.TEXT,
        name="Scaffold Code",
        content="export default function App() {}",
        mime_type="text/javascript",
    )
    assert art.artifact_id == "art_001"
    assert art.artifact_type == ArtifactType.TEXT
    assert art.mime_type == "text/javascript"


def test_multi_dimensional_provider_score():
    score_claude = ProviderScore(provider_id="claude", quality=98.0, availability=99.9, latency_ms=40.0, cost=0.003)
    score_cheap = ProviderScore(provider_id="cheap-llm", quality=75.0, availability=90.0, latency_ms=150.0, cost=0.0001)

    assert score_claude.score > score_cheap.score


def test_selection_strategies_package(sample_context):
    p_cheap = MockProviderAdapter("cheap", cost_per_1k_tokens=0.001)
    p_local = MockProviderAdapter("ollama-local", cost_per_1k_tokens=0.000)
    p_smart = MockProviderAdapter("smart-llm", cost_per_1k_tokens=0.005, features=ProviderFeatureSet(reasoning=True))

    candidates = [p_cheap, p_local, p_smart]

    cost_strat = LowestCostStrategy()
    assert cost_strat.select_provider(candidates, sample_context).provider_id == "ollama-local"

    local_strat = LocalOnlyStrategy()
    assert local_strat.select_provider(candidates, sample_context).provider_id == "ollama-local"

    quality_strat = HighestQualityStrategy()
    assert quality_strat.select_provider(candidates, sample_context).provider_id == "smart-llm"


def test_tool_definition_and_call_schemas():
    tool_def = ToolDefinition(
        name="search_web",
        description="Search public web",
        parameters_schema={"type": "object", "properties": {"query": {"type": "string"}}},
    )
    assert tool_def.name == "search_web"

    tool_call = ToolCall(
        call_id="call_001",
        function_name="search_web",
        arguments={"query": "Next.js 14 blueprint"},
    )
    assert tool_call.call_id == "call_001"
    assert tool_call.arguments["query"] == "Next.js 14 blueprint"
