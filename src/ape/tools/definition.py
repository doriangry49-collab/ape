"""
ToolDefinition & Parameter Schemas — ORION-117.0 Specification.
Defines immutable, behaviorless tool metadata contracts, risk levels, and permission declarations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RiskLevel(str, Enum):
    """Execution risk tier for security policy evaluation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ToolPermission:
    """Capability / scope permission required by a tool."""
    scope: str
    action: str
    resource: Optional[str] = None


@dataclass(frozen=True)
class ToolDefinition:
    """Canonical immutable, behaviorless declaration of an invokable tool."""
    name: str
    version: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    permissions: List[ToolPermission] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    timeout_ms: float = 30000.0
    metadata: Dict[str, Any] = field(default_factory=dict)
