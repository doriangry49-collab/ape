"""
ExecutionArtifact Specification — ORION-114 Specification.
Defines ArtifactType enum and ExecutionArtifact model for multi-modal output management.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ArtifactType(str, Enum):
    """Execution artifact content classification type."""
    TEXT = "text"
    JSON = "json"
    IMAGE = "image"
    FILE = "file"
    TOOL_OUTPUT = "tool_output"
    DIFF = "diff"
    PATCH = "patch"


@dataclass(frozen=True)
class ExecutionArtifact:
    """Immutable multi-modal artifact produced during capability execution."""
    artifact_id: str
    artifact_type: ArtifactType
    name: str
    content: Any
    mime_type: str = "text/plain"
    metadata: Dict[str, Any] = field(default_factory=dict)
