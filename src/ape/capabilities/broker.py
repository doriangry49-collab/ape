"""
CapabilityBroker Pure Facade — ORION-111B / ORION-112 / ORION-113 / ORION-114 / ORION-115 Specification.
Pure facade delegating request planning to ExecutionPlanner, scheduling to ExecutionScheduler, and execution to ExecutionEngine.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from ape.capabilities.budget import ExecutionBudget, ExecutionUsage
from ape.capabilities.contracts import (
    CapabilityResult,
    ExecutionContext,
    ExecutionPolicy,
    ExecutionResult,
)
from ape.capabilities.pipeline import (
    ExecutionEngine,
)
from ape.capabilities.planner import ExecutionPlanner, StandardExecutionPlanner
from ape.capabilities.registry import CapabilityMatrix, CapabilityRegistry, ProviderRegistry
from ape.capabilities.request import ExecutionRequest
from ape.capabilities.resiliency import (
    EventBus,
    ProviderCircuitBreaker,
    RetryStrategy,
    RuntimeEvent,
)
from ape.capabilities.scheduler import ExecutionScheduler, SequentialScheduler
from ape.capabilities.selection import ProviderSelectionStrategy
from ape.prompts.template import RenderedPrompt


@dataclass(frozen=True)
class BrokerDecision:
    """Immutable record of CapabilityBroker selection decision."""
    strategy: str
    candidate_count: int
    selected_provider_id: str
    selection_reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "candidate_count": self.candidate_count,
            "selected_provider": self.selected_provider_id,
            "selection_reason": self.selection_reason,
        }


class CapabilityBroker:
    """
    Pure Facade CapabilityBroker delegating planning to ExecutionPlanner, scheduling to ExecutionScheduler, and execution to ExecutionEngine.
    """

    def __init__(
        self,
        capability_registry: Optional[CapabilityRegistry] = None,
        provider_registry: Optional[ProviderRegistry] = None,
        capability_matrix: Optional[CapabilityMatrix] = None,
        circuit_breaker: Optional[ProviderCircuitBreaker] = None,
        event_bus: Optional[EventBus] = None,
        execution_engine: Optional[ExecutionEngine] = None,
        planner: Optional[ExecutionPlanner] = None,
        scheduler: Optional[ExecutionScheduler] = None,
    ) -> None:
        self.capability_registry = capability_registry or CapabilityRegistry()
        self.provider_registry = provider_registry or ProviderRegistry()
        self.capability_matrix = capability_matrix or CapabilityMatrix(self.provider_registry)
        self.circuit_breaker = circuit_breaker or ProviderCircuitBreaker()
        self.event_bus = event_bus or EventBus()
        self.execution_engine = execution_engine or ExecutionEngine()
        self.planner = planner or StandardExecutionPlanner()
        self.scheduler = scheduler or SequentialScheduler()

    def add_event_hook(self, hook: Callable[[RuntimeEvent], None]) -> None:
        self.event_bus.subscribe(hook)

    def execute_request(self, request: ExecutionRequest) -> ExecutionResult:
        """Pure facade method executing ExecutionRequest via Planner, Graph, and Scheduler."""
        graph = self.planner.plan(request, self.capability_matrix, self.capability_registry, self.circuit_breaker)
        res = self.scheduler.schedule(graph, request, self.execution_engine)

        if res.trace():
            for evt in res.trace().events:
                self.event_bus.publish(evt)

        return res

    def execute(
        self,
        capability_id: str,
        rendered_prompt: RenderedPrompt,
        context: ExecutionContext,
        budget: Optional[ExecutionBudget] = None,
        policy: Optional[ExecutionPolicy] = None,
        usage: Optional[ExecutionUsage] = None,
        strategy: Optional[ProviderSelectionStrategy] = None,
        retry_strategy: Optional[RetryStrategy] = None,
    ) -> CapabilityResult:
        """Backwards compatible facade method."""
        req = ExecutionRequest(
            request_id=f"req_{context.execution_id}",
            capability_id=capability_id,
            rendered_prompt=rendered_prompt,
            context=context,
            policy=policy or ExecutionPolicy(),
            budget=budget or ExecutionBudget(),
        )

        res = self.execute_request(req)
        final_res = res.final()

        if usage:
            usage.record_execution(final_res)
            usage.validate_budget(budget or ExecutionBudget())

        return final_res

    def execute_pipeline(
        self,
        capability_id: str,
        rendered_prompt: RenderedPrompt,
        context: ExecutionContext,
        policy: Optional[ExecutionPolicy] = None,
        strategy: Optional[ProviderSelectionStrategy] = None,
    ) -> ExecutionResult:
        """Backwards compatible facade method returning unified ExecutionResult."""
        req = ExecutionRequest(
            request_id=f"req_{context.execution_id}",
            capability_id=capability_id,
            rendered_prompt=rendered_prompt,
            context=context,
            policy=policy or ExecutionPolicy(),
        )
        return self.execute_request(req)

    def execute_capability(
        self,
        request: Any,  # CapabilityRequest
        context: ExecutionContext,
        governed_planner: Optional[Any] = None,
    ) -> ExecutionResult:
        """
        Governed entry point executing CapabilityRequest via GovernedExecutionPlanner.
        Legacy execute() remains untouched for backwards compatibility.
        """
        from ape.capabilities.governance.planner import GovernedExecutionPlanner
        from ape.prompts.template import RenderedPrompt

        planner = governed_planner or GovernedExecutionPlanner(
            capability_registry=getattr(self, "governance_registry", None),
            binding_resolver=getattr(self, "binding_resolver", None),
        )
        graph = planner.plan_governed(request, context)

        # Wrap CapabilityRequest into ExecutionRequest for SequentialScheduler compatibility
        rendered_prompt = RenderedPrompt(
            system_prompt="",
            user_prompt=str(dict(request.input_payload)),
            prompt_id="governed_prompt",
            version="1.0.0",
            template_sha256="gov_template",
            rendered_sha256="gov_rendered",
            trace_id=context.trace_id,
        )
        exec_req = ExecutionRequest(
            request_id=request.request_id,
            capability_id=request.capability_id,
            rendered_prompt=rendered_prompt,
            context=context,
            policy=ExecutionPolicy(),
        )


        res = self.scheduler.schedule(graph, exec_req, self.execution_engine)

        if res.trace():
            for evt in res.trace().events:
                self.event_bus.publish(evt)

        return res
