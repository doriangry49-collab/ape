"""
Agent Manifest Data Structures — RFC-022 / PR-A1 Specification.
Defines AgentManifest structure for declarative agent roles and capabilities.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AgentManifest:
    """Declarative manifest structure for a Fabric Agent."""
    name: str
    role: str
    version: str = "1.0.0"
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "version": self.version,
            "description": self.description,
            "capabilities": self.capabilities,
            "permissions": self.permissions,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentManifest":
        return cls(
            name=str(data.get("name", "unknown_agent")),
            role=str(data.get("role", "worker")),
            version=str(data.get("version", "1.0.0")),
            description=str(data.get("description", "")),
            capabilities=list(data.get("capabilities", [])),
            permissions=list(data.get("permissions", [])),
            metadata=dict(data.get("metadata", {})),
        )
