"""
Capability ↔ Tool ↔ Execution Integration Package — ORION-118 Specification.
Exports Resolution, Pure Event Transformer, Effective Policy Gate, Evaluator Bridge, and ToolExecutionStage.
"""

from ape.capabilities.integration.contracts import (
    CapabilityToolResolver,
    ResolutionResult,
    ToolCandidate,
    ToolExecutionEvent,
    ToolResultExecutionMapper,
)
from ape.capabilities.integration.evaluator_bridge import EffectiveToolPolicyEvaluator
from ape.capabilities.integration.policy_gate import (
    AuthorizationDecision,
    AuthorizationDecisionType,
    EffectivePolicyGate,
    PermissionState,
)
from ape.capabilities.integration.stage import ToolExecutionStage

__all__ = [
    "ToolCandidate",
    "ResolutionResult",
    "CapabilityToolResolver",
    "ToolExecutionEvent",
    "ToolResultExecutionMapper",
    "PermissionState",
    "AuthorizationDecisionType",
    "AuthorizationDecision",
    "EffectivePolicyGate",
    "EffectiveToolPolicyEvaluator",
    "ToolExecutionStage",
]
