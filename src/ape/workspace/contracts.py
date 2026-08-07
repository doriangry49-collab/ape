"""
Workspace Operating System Core Contracts — RFC-022 / PR-W1 Specification.
Defines WorkspaceContext and WorkspaceManifest schemas for multi-tenant project isolation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class WorkspaceContext:
    """Immutable context representing active workspace configuration."""
    name: str
    slug: str
    root_path: Path
    active: bool = True
    created_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "slug": self.slug,
            "root_path": str(self.root_path),
            "active": self.active,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass
class WorkspaceManifest:
    """Declarative workspace manifest structure."""
    name: str
    description: str = ""
    projects: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "projects": self.projects,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkspaceManifest":
        return cls(
            name=str(data.get("name", "default")),
            description=str(data.get("description", "")),
            projects=list(data.get("projects", [])),
            tags=list(data.get("tags", [])),
            metadata=dict(data.get("metadata", {})),
        )
