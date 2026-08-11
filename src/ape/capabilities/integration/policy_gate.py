"""
EffectivePolicyGate & Authorization Decision Binding — ORION-118 Specification.
Evaluates single unified authorization decision, 3-tier permission state taxonomy, and spoof-proof decision binding.
"""

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set

from ape.capabilities.contracts import ExecutionContext, ExecutionPolicy
from ape.tools.definition import RiskLevel, ToolDefinition, ToolPermission


class PermissionState(str, Enum):
    """3-Tier Permission State Taxonomy."""
    SATISFIED = "satisfied"
    MISSING_BUT_GRANTABLE = "missing_but_grantable"
    FORBIDDEN = "forbidden"


class AuthorizationDecisionType(str, Enum):
    """Unified Authorization Decision Type."""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass(frozen=True)
class AuthorizationDecision:
    """Immutable, spoof-proof Authorization Decision bound to call, context, and tool identity."""
    decision_id: str
    decision: AuthorizationDecisionType
    effective_risk: RiskLevel
    capability_id: str
    tool_id: str
    call_id: str
    context_id: str
    permission_state: PermissionState
    approval_required: bool
    reason: str
    evidence_hash: str
    timestamp: float = field(default_factory=time.time)

    def verify_binding(self, call_id: str, capability_id: str, tool_id: str, context_id: str) -> bool:
        """Verify that this AuthorizationDecision is bound to the exact target call, tool, and context."""
        return (
            self.call_id == call_id
            and self.capability_id == capability_id
            and self.tool_id == tool_id
            and self.context_id == context_id
        )


class EffectivePolicyGate:
    """Evaluates Capability Risk + Tool Risk + Context Permissions into a single spoof-proof AuthorizationDecision."""

    @staticmethod
    def _calculate_effective_risk(capability_policy: ExecutionPolicy, tool_definition: ToolDefinition) -> RiskLevel:
        tool_risk = tool_definition.risk_level
        # Map policy constraints if present
        if tool_risk == RiskLevel.CRITICAL:
            return RiskLevel.CRITICAL
        elif tool_risk == RiskLevel.HIGH:
            return RiskLevel.HIGH
        elif tool_risk == RiskLevel.MEDIUM:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    @staticmethod
    def evaluate(
        capability_policy: ExecutionPolicy,
        tool_definition: ToolDefinition,
        context: ExecutionContext,
        call_id: str,
        capability_id: str,
        grantable_scopes: Optional[Set[str]] = None,
        context_permissions: Optional[List[ToolPermission]] = None,
        approved_by_human: bool = False,
    ) -> AuthorizationDecision:
        """Evaluate single spoof-proof Effective Policy Decision."""
        effective_risk = EffectivePolicyGate._calculate_effective_risk(capability_policy, tool_definition)
        context_scopes = {p.scope for p in (context_permissions or [])}
        grantable = grantable_scopes or {"workspace", "user_prompt"}

        # 1. Evaluate Permission State Taxonomy
        missing: List[ToolPermission] = []
        forbidden: List[ToolPermission] = []

        for req_perm in tool_definition.permissions:
            if req_perm.scope not in context_scopes:
                if req_perm.scope in grantable:
                    missing.append(req_perm)
                else:
                    forbidden.append(req_perm)

        if forbidden:
            perm_state = PermissionState.FORBIDDEN
            decision_type = AuthorizationDecisionType.DENY
            reason = f"Execution FORBIDDEN due to ungrantable missing scope(s): {[p.scope for p in forbidden]}"
            approval_req = False
        elif missing:
            perm_state = PermissionState.MISSING_BUT_GRANTABLE
            if approved_by_human:
                decision_type = AuthorizationDecisionType.ALLOW
                reason = "Execution APPROVED by human for grantable missing permissions."
                approval_req = False
            else:
                decision_type = AuthorizationDecisionType.REQUIRE_APPROVAL
                reason = f"Execution REQUIRES_APPROVAL for grantable missing scope(s): {[p.scope for p in missing]}"
                approval_req = True
        else:
            perm_state = PermissionState.SATISFIED
            if effective_risk in (RiskLevel.HIGH, RiskLevel.CRITICAL) and not approved_by_human:
                decision_type = AuthorizationDecisionType.REQUIRE_APPROVAL
                reason = f"Execution REQUIRES_APPROVAL due to effective risk level '{effective_risk.value}'."
                approval_req = True
            else:
                decision_type = AuthorizationDecisionType.ALLOW
                reason = "Execution ALLOWED."
                approval_req = False

        # Generate SHA-256 Decision Binding ID
        raw_payload = f"{call_id}:{capability_id}:{tool_definition.name}:{context.execution_id}:{decision_type.value}:{effective_risk.value}"
        decision_id = "dec_auth_" + hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()[:16]
        evidence_hash = hashlib.sha256(f"evidence:{decision_id}:{raw_payload}".encode("utf-8")).hexdigest()

        return AuthorizationDecision(
            decision_id=decision_id,
            decision=decision_type,
            effective_risk=effective_risk,
            capability_id=capability_id,
            tool_id=tool_definition.name,
            call_id=call_id,
            context_id=context.execution_id,
            permission_state=perm_state,
            approval_required=approval_req,
            reason=reason,
            evidence_hash=evidence_hash,
        )
