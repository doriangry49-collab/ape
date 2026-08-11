"""
Governed Execution Planner Contract — ORION-119.1 Specification.
Translates CapabilityRequest into governed ExecutionGraph with upfront Risk Aggregation,
Single Authorization Decision, and zero caller target selection bypass.
"""

from typing import List, Optional

from ape.capabilities.contracts import ExecutionContext, ExecutionState
from ape.capabilities.governance.binding import BindingType, CapabilityBinding
from ape.capabilities.governance.composite import CompositeCapabilityDefinition
from ape.capabilities.governance.descriptor import CapabilityDescriptor, CapabilityType
from ape.capabilities.governance.policy import CapabilityPolicyEvaluator
from ape.capabilities.governance.registry import CapabilityRegistry
from ape.capabilities.governance.request import CapabilityRequest
from ape.capabilities.governance.resolver import CapabilityBindingResolver
from ape.capabilities.graph import ExecutionGraph, ExecutionNode
from ape.capabilities.integration.contracts import ToolResultExecutionMapper
from ape.capabilities.integration.evaluator_bridge import EffectiveToolPolicyEvaluator
from ape.capabilities.integration.policy_gate import (
    AuthorizationDecision,
    AuthorizationDecisionType,
)
from ape.capabilities.integration.stage import ToolExecutionStage
from ape.capabilities.pipeline import BaseExecutionStage
from ape.capabilities.resiliency import RuntimeEvent
from ape.tools.contracts import ToolCallPayload
from ape.tools.definition import RiskLevel
from ape.tools.executor import ToolExecutor


class GovernedExecutionNodeStage(BaseExecutionStage):
    """
    Stage wrapper for governed atomic or composite capability node execution.
    Executes tool via ToolExecutor with injected EffectiveToolPolicyEvaluator bridge (0 double authorization).
    """
    stage_name: str = "GovernedExecutionNodeStage"

    def __init__(
        self,
        descriptor: CapabilityDescriptor,
        binding: CapabilityBinding,
        decision: AuthorizationDecision,
        executor: Optional[ToolExecutor] = None,
    ) -> None:
        self.descriptor = descriptor
        self.binding = binding
        self.decision = decision
        self.executor = executor or ToolExecutor()

    def execute(self, state: ExecutionState) -> ExecutionState:
        # 119.2.B Execution-Time Live Lifecycle Check
        from ape.capabilities.contracts import CapabilityError
        from ape.capabilities.governance.registry import CapabilityLifecycleState


        if hasattr(self, "capability_registry") and self.capability_registry:
            reg = self.capability_registry
        else:
            reg = getattr(self.executor, "governance_registry", None)

        if reg and hasattr(reg, "get_lifecycle_state"):
            try:
                l_state = reg.get_lifecycle_state(self.descriptor.qualified_id)
                if l_state == CapabilityLifecycleState.REVOKED:
                    raise CapabilityError(
                        f"FAIL CLOSED: Capability '{self.descriptor.qualified_id}' is REVOKED at execution time."
                    )
                elif l_state == CapabilityLifecycleState.DEPRECATED:
                    state.trace_events.append(
                        RuntimeEvent(
                            event_type="CapabilityDeprecatedWarning",
                            capability_id=self.descriptor.qualified_id,
                            trace_id=state.context.trace_id,
                            details={"message": f"Capability '{self.descriptor.qualified_id}' is DEPRECATED but permitted."},
                        )
                    )
            except CapabilityError:
                raise
            except Exception:
                pass

        # Record entry trace event
        state.trace_events.append(
            RuntimeEvent(
                event_type="GovernedCapabilityStarted",
                capability_id=self.descriptor.qualified_id,
                trace_id=state.context.trace_id,
                details={
                    "binding_id": self.binding.binding_id,
                    "policy_decision_id": self.decision.decision_id,
                    "effective_risk": self.decision.effective_risk.value,
                },
            )
        )


        if self.binding.binding_type == BindingType.TOOL:
            # 1. Prepare bridge with pre-evaluated AuthorizationDecision
            bridge = EffectiveToolPolicyEvaluator()
            call_id = self.decision.call_id
            bridge.set_active_decision(
                decision=self.decision,
                call_id=call_id,
                capability_id=self.descriptor.qualified_id,
                context_id=state.context.execution_id,
            )


            # Ingest bridge into ToolExecutor
            tool_executor = ToolExecutor(policy_evaluator=bridge)
            # Register native reference tool if available in registry
            try:
                tool_def = self.executor.registry.resolve_tool(self.binding.target_id)
                tool_executor.registry.register_tool(tool_def)
                if self.binding.target_id in self.executor._adapters:
                    tool_executor.register_adapter(self.executor._adapters[self.binding.target_id])
            except Exception:
                pass


            input_args = state.working_memory.get("input_payload")
            if input_args is None and hasattr(state, "rendered_prompt"):
                if hasattr(state.rendered_prompt, "variables") and state.rendered_prompt.variables:
                    input_args = state.rendered_prompt.variables
                elif hasattr(state.rendered_prompt, "user_prompt") and state.rendered_prompt.user_prompt:
                    try:
                        import ast
                        input_args = ast.literal_eval(state.rendered_prompt.user_prompt)
                    except Exception:
                        pass
            payload = ToolCallPayload(
                call_id=call_id,
                tool_name=self.binding.target_id,
                arguments=input_args if isinstance(input_args, dict) else {},
            )



            # Stage 3 in ToolExecutor runs verify_binding() integrity check
            tool_result = tool_executor.execute(
                payload=payload,
                approved_by_human=(self.decision.decision == AuthorizationDecisionType.ALLOW),
            )

            # 2. Map pure ToolResult -> ToolExecutionEvent
            event = ToolResultExecutionMapper.map_to_event(tool_result)


            # 3. Apply event to ExecutionState
            tool_stage = ToolExecutionStage(event=event)
            state = tool_stage.execute(state)
            state.result = tool_result

        return state


class GovernedExecutionPlanner:
    """
    Pure Graph Translator planning governed ExecutionGraph topology from CapabilityRequest contract.
    Enforces upfront Risk Aggregation, Single Authorization Decision, and zero caller target selection bypass.
    """
    planner_name: str = "GOVERNED_PLANNER"

    def __init__(
        self,
        capability_registry: Optional[CapabilityRegistry] = None,
        binding_resolver: Optional[CapabilityBindingResolver] = None,
        tool_executor: Optional[ToolExecutor] = None,
    ) -> None:
        self.capability_registry = capability_registry or CapabilityRegistry()
        self.binding_resolver = binding_resolver or CapabilityBindingResolver()
        self.tool_executor = tool_executor or ToolExecutor()

    def plan_governed(self, request: CapabilityRequest, context: ExecutionContext) -> ExecutionGraph:
        """
        Translate CapabilityRequest into a governed ExecutionGraph without executing tools or schedulers.
        """
        # 1. Resolve capability descriptor and binding
        descriptor = self.capability_registry.resolve_version(request.capability_id, request.version_constraint)
        binding = self.binding_resolver.resolve_binding(descriptor)

        graph = ExecutionGraph(graph_id=f"graph_gov_{request.request_id}")

        if descriptor.capability_type == CapabilityType.ATOMIC:
            # Single Authorization Decision
            decision = CapabilityPolicyEvaluator.evaluate_effective_authorization(
                request_id=request.request_id,
                descriptor=descriptor,
                binding=binding,
                context=context,
                call_id=f"call_{request.request_id}",
            )

            node_stage = GovernedExecutionNodeStage(
                descriptor=descriptor,
                binding=binding,
                decision=decision,
                executor=self.tool_executor,
            )
            node_stage.capability_registry = self.capability_registry
            node = ExecutionNode(node_id=f"node_{descriptor.capability_id}", operation=node_stage)
            graph.add_node(node)

        elif descriptor.capability_type == CapabilityType.COMPOSITE:
            # Composite resolution: aggregate child risks upfront for Single Authorization Decision
            composite_def: Optional[CompositeCapabilityDefinition] = descriptor.metadata.get("composite_definition")
            child_descriptors: List[CapabilityDescriptor] = []
            child_risks: List[RiskLevel] = []

            if composite_def:
                for c_node in composite_def.nodes:
                    c_desc = self.capability_registry.resolve_version(c_node.capability_id, c_node.version_constraint)
                    child_descriptors.append(c_desc)
                    child_risks.append(c_desc.risk_tier)

            # Risk Monotonicity: Effective Risk = MAX(Parent, Children, Tool, Context)
            decision = CapabilityPolicyEvaluator.evaluate_effective_authorization(
                request_id=request.request_id,
                descriptor=descriptor,
                binding=binding,
                context=context,
                call_id=f"call_{request.request_id}",
                child_risks=child_risks,
            )

            # Translate Composite nodes to ExecutionGraph
            if composite_def:
                for c_node in composite_def.nodes:
                    c_desc = self.capability_registry.resolve_version(c_node.capability_id, c_node.version_constraint)
                    c_bind = self.binding_resolver.resolve_binding(c_desc)
                    c_stage = GovernedExecutionNodeStage(
                        descriptor=c_desc,
                        binding=c_bind,
                        decision=decision,  # Share single effective decision identity
                        executor=self.tool_executor,
                    )
                    c_stage.capability_registry = self.capability_registry
                    ex_node = ExecutionNode(node_id=c_node.node_id, operation=c_stage)
                    graph.add_node(ex_node)


                for src, tgt in composite_def.edges:
                    graph.add_edge(src, tgt)

        return graph
