"""
Pluggable ExecutionEngine & Stage Lifecycle Pipeline — ORION-114 Specification.
Provides ExecutionStage Protocol (before, execute, after, rollback), ExecutionMiddleware Protocol,
and DAG-ready ExecutionEngine stage runner.
"""

import time
from typing import Any, Callable, List, Optional, Protocol, runtime_checkable

from ape.capabilities.adapters_base import ProviderFeatureSet
from ape.capabilities.contracts import (
    ExecutionResult,
    ExecutionState,
    ProviderUnavailableError,
    RuntimeContext,
)
from ape.capabilities.resiliency import CircuitBreakerState, ProviderEndpointKey, RuntimeEvent
from ape.capabilities.selection import LowestCostStrategy, ProviderSelectionStrategy
from ape.capabilities.trace import ExecutionTrace


@runtime_checkable
class ExecutionStage(Protocol):
    """Canonical ExecutionStage lifecycle interface supporting compensation rollback."""
    stage_name: str

    def before(self, state: ExecutionState) -> ExecutionState:
        """Pre-execution hook."""
        ...

    def execute(self, state: ExecutionState) -> ExecutionState:
        """Main stage execution logic."""
        ...

    def after(self, state: ExecutionState) -> ExecutionState:
        """Post-execution hook."""
        ...

    def rollback(self, state: ExecutionState) -> ExecutionState:
        """Compensation rollback logic on stage failure."""
        ...


@runtime_checkable
class ExecutionMiddleware(Protocol):
    """Middleware interface wrapping stage execution pipeline."""

    def process(self, state: ExecutionState, next_fn: Callable[[ExecutionState], ExecutionState]) -> ExecutionState:
        ...


class BaseExecutionStage:
    """Base implementation providing default empty before, after, and rollback hooks."""
    stage_name: str = "BaseStage"

    def before(self, state: ExecutionState) -> ExecutionState:
        return state

    def execute(self, state: ExecutionState) -> ExecutionState:
        return state

    def after(self, state: ExecutionState) -> ExecutionState:
        return state

    def rollback(self, state: ExecutionState) -> ExecutionState:
        return state


class ResolveCandidateStage(BaseExecutionStage):
    """Resolves candidate ProviderAdapters matching capability_id and ProviderFeatureSet requirements."""
    stage_name: str = "ResolveCandidateStage"

    def __init__(self, capability_matrix: Any, capability_registry: Any) -> None:
        self.capability_matrix = capability_matrix
        self.capability_registry = capability_registry

    def execute(self, state: ExecutionState) -> ExecutionState:
        state.trace_events.append(
            RuntimeEvent("CapabilityRequested", state.capability_id, state.context.trace_id)
        )
        candidates = self.capability_matrix.get_candidate_adapters(state.capability_id)
        state.candidates = candidates
        return state


class PolicyEnforcementStage(BaseExecutionStage):
    """Enforces required features matching and CircuitBreaker health checks."""
    stage_name: str = "PolicyEnforcementStage"

    def __init__(self, circuit_breaker: Any = None, policy: Any = None) -> None:
        from ape.capabilities.resiliency import ProviderCircuitBreaker

        self.circuit_breaker = circuit_breaker or ProviderCircuitBreaker()
        self.policy = policy

    def execute(self, state: ExecutionState) -> ExecutionState:
        policy = self.policy or getattr(state, "policy", None)
        if policy and policy.required_features:
            req_set = ProviderFeatureSet(**{f: True for f in policy.required_features if hasattr(ProviderFeatureSet, f)})
            state.candidates = [a for a in state.candidates if a.features().is_subset(req_set)]

        if not state.candidates:
            raise ProviderUnavailableError(f"No candidate providers available for capability '{state.capability_id}'.")

        allowed = []
        for adapter in state.candidates:
            endpoint_key = ProviderEndpointKey(adapter.provider_id, adapter.profile.display_name)
            if self.circuit_breaker.get_state(endpoint_key) != CircuitBreakerState.OPEN:
                allowed.append(adapter)

        state.candidates = allowed
        if not state.candidates:
            raise ProviderUnavailableError(f"All candidate providers for capability '{state.capability_id}' are blocked by OPEN CircuitBreaker.")

        return state


class StrategySelectionStage(BaseExecutionStage):
    """Executes ProviderSelectionStrategy to choose target ProviderAdapter."""
    stage_name: str = "StrategySelectionStage"

    def __init__(self, strategy: Optional[ProviderSelectionStrategy] = None) -> None:
        self.strategy = strategy or LowestCostStrategy()

    def execute(self, state: ExecutionState) -> ExecutionState:
        selected = self.strategy.select_provider(state.candidates, state.context)
        state.selected_provider = selected
        state.runtime.selected_provider_id = selected.provider_id
        state.trace_events.append(
            RuntimeEvent(
                "ProviderSelected",
                state.capability_id,
                state.context.trace_id,
                provider_id=selected.provider_id,
                details={"strategy": self.strategy.strategy_name},
            )
        )
        return state


class AdapterExecutionStage(BaseExecutionStage):
    """Dispatches execution to selected ProviderAdapter."""
    stage_name: str = "AdapterExecutionStage"

    def execute(self, state: ExecutionState) -> ExecutionState:
        selected = state.selected_provider
        state.trace_events.append(
            RuntimeEvent("ExecutionStarted", state.capability_id, state.context.trace_id, provider_id=selected.provider_id)
        )
        try:
            res = selected.execute(state.rendered_prompt, state.capability_id, state.context)
            state.result = res
            state.trace_events.append(
                RuntimeEvent(
                    "ExecutionCompleted",
                    state.capability_id,
                    state.context.trace_id,
                    provider_id=selected.provider_id,
                    details={"cost": res.cost, "duration_ms": res.duration_ms},
                )
            )
        except Exception as exc:
            state.trace_events.append(
                RuntimeEvent(
                    "ExecutionFailed",
                    state.capability_id,
                    state.context.trace_id,
                    provider_id=selected.provider_id,
                    details={"error": str(exc)},
                )
            )
            raise
        return state


class ExecutionEngine:
    """Pluggable DAG-ready ExecutionEngine running pipeline stages with before/execute/after/rollback hooks."""

    def __init__(self, stages: Optional[List[ExecutionStage]] = None) -> None:
        self.stages: List[ExecutionStage] = stages or []
        self.middlewares: List[ExecutionMiddleware] = []

    def add_stage(self, stage: ExecutionStage) -> None:
        """Register a stage into execution pipeline."""
        self.stages.append(stage)

    def add_middleware(self, middleware: ExecutionMiddleware) -> None:
        """Register a middleware into execution pipeline."""
        self.middlewares.append(middleware)

    def create_runtime_context(self, request: Any) -> RuntimeContext:
        """Create dynamic RuntimeContext for an ExecutionRequest."""
        return RuntimeContext(
            execution_id=request.context.execution_id,
            trace_id=request.context.trace_id,
            timeout_ms=request.policy.timeout_ms if hasattr(request, "policy") and request.policy else 30000.0,
        )

    def execute_pipeline(self, initial_state: ExecutionState) -> ExecutionResult:
        """Execute all registered pipeline stages sequentially."""
        state = initial_state
        executed_stages: List[ExecutionStage] = []

        start_time = time.time()

        for stage in self.stages:
            try:
                state = stage.before(state)
                state = stage.execute(state)
                state = stage.after(state)
                executed_stages.append(stage)
            except Exception as exc:
                # Execute compensation rollback in reverse order
                for st in reversed(executed_stages):
                    try:
                        state = st.rollback(state)
                    except Exception:
                        pass
                raise exc

        dur_ms = round((time.time() - start_time) * 1000.0, 2)
        trace = ExecutionTrace(
            trace_id=state.context.trace_id,
            capability_id=state.capability_id,
            execution_id=state.context.execution_id,
            events=state.trace_events,
            duration_ms=dur_ms,
        )

        return ExecutionResult(capability_result=state.result, trace=trace)
