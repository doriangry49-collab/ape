"""
Tool Policy & Authorization Evaluator — ORION-117.0 Specification.
Evaluates authorization, required permissions, risk tiers, and human approval gates prior to execution.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from ape.tools.definition import RiskLevel, ToolDefinition, ToolPermission


class PolicyDecision(str, Enum):
    """Authorization evaluation decision."""
    AUTHORIZED = "authorized"
    DENIED = "denied"
    APPROVAL_REQUIRED = "approval_required"


@dataclass(frozen=True)
class PolicyEvaluationResult:
    """Outcome of a tool policy evaluation."""
    decision: PolicyDecision
    reason: str
    risk_level: RiskLevel
    missing_permissions: List[ToolPermission] = field(default_factory=list)


class ToolPolicyEvaluator:
    """Evaluates tool execution authorization against context permissions and risk tiers."""

    def __init__(self, allowed_scopes: Optional[Set[str]] = None, max_auto_risk_level: RiskLevel = RiskLevel.MEDIUM) -> None:
        self.allowed_scopes = allowed_scopes if allowed_scopes is not None else {"*"}
        self.max_auto_risk_level = max_auto_risk_level

    def evaluate(
        self,
        definition: ToolDefinition,
        context_permissions: Optional[List[ToolPermission]] = None,
        approved_by_human: bool = False,
    ) -> PolicyEvaluationResult:
        """Evaluate if definition is authorized given context permissions and risk tier."""

        # 1. Check Permissions
        context_scopes = {p.scope for p in (context_permissions or [])}
        missing: List[ToolPermission] = []

        if "*" not in self.allowed_scopes:
            for req_perm in definition.permissions:
                if req_perm.scope not in self.allowed_scopes and req_perm.scope not in context_scopes:
                    missing.append(req_perm)

        if missing:
            return PolicyEvaluationResult(
                decision=PolicyDecision.DENIED,
                reason=f"Missing required permissions: {[p.scope for p in missing]}",
                risk_level=definition.risk_level,
                missing_permissions=missing,
            )

        # 2. Check Risk Level & Approval Requirement
        if definition.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            if not approved_by_human:
                return PolicyEvaluationResult(
                    decision=PolicyDecision.APPROVAL_REQUIRED,
                    reason=f"Tool risk level '{definition.risk_level.value}' requires explicit human approval.",
                    risk_level=definition.risk_level,
                )

        return PolicyEvaluationResult(
            decision=PolicyDecision.AUTHORIZED,
            reason="Tool execution authorized.",
            risk_level=definition.risk_level,
        )
