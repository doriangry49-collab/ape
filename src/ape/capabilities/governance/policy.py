"""
Capability Risk Inheritance & Authorization Decision Identity Contract — ORION-119.D & 119.4 Specification.
Enforces Risk Monotonicity across Composite Nodes and generates canonical policy_decision_id.
"""

from dataclasses import dataclass, field
import hashlib
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from ape.capabilities.contracts import ExecutionContext, ExecutionPolicy
from ape.capabilities.governance.binding import CapabilityBinding
from ape.capabilities.governance.descriptor import CapabilityDescriptor
from ape.capabilities.integration.policy_gate import AuthorizationDecision, AuthorizationDecisionType, PermissionState
from ape.tools.definition import RiskLevel, ToolPermission

# Risk Tier Order for Risk Monotonicity (LOW -> MEDIUM -> HIGH -> CRITICAL)
RISK_ORDER = {
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4,
}

_ORDER_TO_RISK = {v: k for k, v in RISK_ORDER.items()}


class CapabilityPolicyEvaluator:
    """Evaluates Capability Policy, Composite Risk Inheritance, and generates canonical policy_decision_id."""

    @staticmethod
    def calculate_effective_risk(
        capability_risk: RiskLevel,
        child_risks: Optional[List[RiskLevel]] = None,
        tool_risk: Optional[RiskLevel] = None,
        context_risk: Optional[RiskLevel] = None,
    ) -> RiskLevel:
        """
        Enforce Risk Monotonicity: Effective Risk = MAX(Capability, Child Risks, Tool Risk, Context Risk).
        No descendant or policy constraint may reduce an inherited risk tier.
        """
        max_level = RISK_ORDER.get(capability_risk, 1)

        if child_risks:
            for cr in child_risks:
                max_level = max(max_level, RISK_ORDER.get(cr, 1))

        if tool_risk:
            max_level = max(max_level, RISK_ORDER.get(tool_risk, 1))

        if context_risk:
            max_level = max(max_level, RISK_ORDER.get(context_risk, 1))

        return _ORDER_TO_RISK[max_level]

    @staticmethod
    def evaluate_effective_authorization(
        request_id: str,
        descriptor: CapabilityDescriptor,
        binding: CapabilityBinding,
        context: ExecutionContext,
        call_id: str,
        child_risks: Optional[List[RiskLevel]] = None,
        tool_risk: Optional[RiskLevel] = None,
        context_permissions: Optional[List[ToolPermission]] = None,
        approved_by_human: bool = False,
    ) -> AuthorizationDecision:
        """
        Evaluate ONE Single Effective Authorization Decision with deterministic policy_decision_id.
        """
        effective_risk = CapabilityPolicyEvaluator.calculate_effective_risk(
            capability_risk=descriptor.risk_tier,
            child_risks=child_risks,
            tool_risk=tool_risk,
        )

        context_scopes = {p.scope for p in (context_permissions or [])}
        missing: List[ToolPermission] = []
        forbidden: List[ToolPermission] = []

        for req_perm in binding.required_permissions:
            if req_perm.scope not in context_scopes:
                if req_perm.scope in binding.allowed_scopes:
                    missing.append(req_perm)
                else:
                    forbidden.append(req_perm)

        if forbidden:
            perm_state = PermissionState.FORBIDDEN
            decision_type = AuthorizationDecisionType.DENY
            reason = f"Execution FORBIDDEN: Missing required ungrantable permission(s): {[p.scope for p in forbidden]}"
            approval_req = False
        elif missing:
            perm_state = PermissionState.MISSING_BUT_GRANTABLE
            if approved_by_human:
                decision_type = AuthorizationDecisionType.ALLOW
                reason = "Execution ALLOWED by human approval for grantable missing permissions."
                approval_req = False
            else:
                decision_type = AuthorizationDecisionType.REQUIRE_APPROVAL
                reason = f"Execution REQUIRES_APPROVAL for grantable missing permission(s): {[p.scope for p in missing]}"
                approval_req = True
        else:
            perm_state = PermissionState.SATISFIED
            if effective_risk in (RiskLevel.HIGH, RiskLevel.CRITICAL) and not approved_by_human:
                decision_type = AuthorizationDecisionType.REQUIRE_APPROVAL
                reason = f"Execution REQUIRES_APPROVAL due to effective risk tier '{effective_risk.value}'."
                approval_req = True
            else:
                decision_type = AuthorizationDecisionType.ALLOW
                reason = "Execution ALLOWED."
                approval_req = False

        # Deterministic policy_decision_id calculation (119.4)
        raw_payload = f"{request_id}:{descriptor.capability_id}:{descriptor.version}:{binding.binding_id}:{effective_risk.value}"
        decision_id = "dec_auth_" + hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()[:16]
        evidence_hash = hashlib.sha256(f"evidence:{decision_id}:{raw_payload}".encode("utf-8")).hexdigest()

        return AuthorizationDecision(
            decision_id=decision_id,
            decision=decision_type,
            effective_risk=effective_risk,
            capability_id=descriptor.qualified_id,
            tool_id=binding.target_id,
            call_id=call_id,
            context_id=context.execution_id,
            permission_state=perm_state,
            approval_required=approval_req,
            reason=reason,
            evidence_hash=evidence_hash,
        )
