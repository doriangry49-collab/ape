"""
EffectiveToolPolicyEvaluator Bridge — ORION-118 Specification.
Injects spoof-proof AuthorizationDecision verification into ToolExecutor Stage 3 (AUTHORIZE)
without modifying frozen ORION-117.0 contracts.
"""

from typing import Any, List, Optional

from ape.capabilities.integration.policy_gate import (
    AuthorizationDecision,
    AuthorizationDecisionType,
)
from ape.tools.definition import ToolDefinition, ToolPermission
from ape.tools.policy import PolicyDecision, PolicyEvaluationResult, ToolPolicyEvaluator


class EffectiveToolPolicyEvaluator(ToolPolicyEvaluator):
    """
    Evaluator bridge plugging into ToolExecutor.__init__(policy_evaluator=...).
    Validates AuthorizationDecision bindings at Stage 3 (AUTHORIZE) without touching frozen 117.0 code.
    """

    def __init__(
        self,
        active_decision: Optional[AuthorizationDecision] = None,
        target_call_id: Optional[str] = None,
        target_capability_id: Optional[str] = None,
        target_context_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.active_decision = active_decision
        self.target_call_id = target_call_id
        self.target_capability_id = target_capability_id
        self.target_context_id = target_context_id

    def set_active_decision(
        self,
        decision: AuthorizationDecision,
        call_id: str,
        capability_id: str,
        context_id: str,
    ) -> None:
        """Bind active AuthorizationDecision to target call parameters."""
        self.active_decision = decision
        self.target_call_id = call_id
        self.target_capability_id = capability_id
        self.target_context_id = context_id

    def evaluate(
        self,
        definition: ToolDefinition,
        context_permissions: Optional[List[ToolPermission]] = None,
        approved_by_human: bool = False,
    ) -> PolicyEvaluationResult:
        """Evaluate authorization against active AuthorizationDecision binding."""
        if self.active_decision is not None:
            # 1. Enforce spoof-proof decision binding verification
            call_id = self.target_call_id or ""
            cap_id = self.target_capability_id or ""
            ctx_id = self.target_context_id or ""

            if not self.active_decision.verify_binding(call_id, cap_id, definition.name, ctx_id):
                return PolicyEvaluationResult(
                    decision=PolicyDecision.DENIED,
                    reason=f"SECURITY_DENIAL: AuthorizationDecision binding verification failed for tool '{definition.name}'. Mismatched call_id/capability_id/context_id.",
                    risk_level=definition.risk_level,
                )

            # 2. Map verified decision type
            if self.active_decision.decision == AuthorizationDecisionType.DENY:
                return PolicyEvaluationResult(
                    decision=PolicyDecision.DENIED,
                    reason=f"DENIED by EffectivePolicyGate: {self.active_decision.reason}",
                    risk_level=self.active_decision.effective_risk,
                )
            elif self.active_decision.decision == AuthorizationDecisionType.REQUIRE_APPROVAL:
                if approved_by_human:
                    return PolicyEvaluationResult(
                        decision=PolicyDecision.AUTHORIZED,
                        reason="Tool execution AUTHORIZED following human approval.",
                        risk_level=self.active_decision.effective_risk,
                    )
                return PolicyEvaluationResult(
                    decision=PolicyDecision.APPROVAL_REQUIRED,
                    reason=f"APPROVAL_REQUIRED by EffectivePolicyGate: {self.active_decision.reason}",
                    risk_level=self.active_decision.effective_risk,
                )
            elif self.active_decision.decision == AuthorizationDecisionType.ALLOW:
                return PolicyEvaluationResult(
                    decision=PolicyDecision.AUTHORIZED,
                    reason=f"AUTHORIZED by EffectivePolicyGate: {self.active_decision.reason}",
                    risk_level=self.active_decision.effective_risk,
                )

        # Fallback to standard 117.0 policy evaluation if no active decision bound
        return super().evaluate(definition, context_permissions=context_permissions, approved_by_human=approved_by_human)
