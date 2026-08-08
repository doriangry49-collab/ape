"""
APE Tool Abstraction Layer — ORION-117.0 Specification.
Exports canonical contracts, lifecycle orchestrator, policies, and registry interfaces.
"""

from ape.tools.adapters.base import BaseToolAdapter
from ape.tools.contracts import (
    ApprovalRequiredError,
    EvidenceSink,
    ToolAuthorizationError,
    ToolCallPayload,
    ToolError,
    ToolExecutionError,
    ToolLifecycleStage,
    ToolNotFoundError,
    ToolResult,
)
from ape.tools.definition import RiskLevel, ToolDefinition, ToolPermission
from ape.tools.executor import DefaultEvidenceSink, ToolExecutor
from ape.tools.policy import PolicyDecision, PolicyEvaluationResult, ToolPolicyEvaluator
from ape.tools.registry import ToolRegistry, ToolScope

__all__ = [
    "RiskLevel",
    "ToolPermission",
    "ToolDefinition",
    "ToolLifecycleStage",
    "ToolError",
    "ToolNotFoundError",
    "ToolAuthorizationError",
    "ApprovalRequiredError",
    "ToolExecutionError",
    "ToolCallPayload",
    "ToolResult",
    "EvidenceSink",
    "DefaultEvidenceSink",
    "PolicyDecision",
    "PolicyEvaluationResult",
    "ToolPolicyEvaluator",
    "ToolScope",
    "ToolRegistry",
    "BaseToolAdapter",
    "ToolExecutor",
]
