"""
Shared Memory & Workspace Context — RFC-022 / PR-A4 Specification.
Provides shared knowledge graph, deliverable context, and artifact state passing across Fabric Agents.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


class SharedMemoryWorkspace:
    """Thread-safe shared memory workspace for inter-agent context sharing."""

    def __init__(self, topic_slug: str, project_root: Optional[Path] = None) -> None:
        self.topic_slug = topic_slug
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self._memory: Dict[str, Any] = {}
        self._artifacts: Dict[str, Any] = {}
        self._findings: List[Dict[str, Any]] = []

    def set(self, key: str, value: Any) -> None:
        """Store key-value in shared memory."""
        self._memory[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve key from shared memory."""
        return self._memory.get(key, default)

    def add_artifact(self, artifact_id: str, artifact_data: Any) -> None:
        """Register deliverable artifact in shared memory workspace."""
        self._artifacts[artifact_id] = artifact_data

    def get_artifact(self, artifact_id: str) -> Any:
        """Retrieve deliverable artifact by ID."""
        return self._artifacts.get(artifact_id)

    def log_finding(self, agent_name: str, role: str, finding: str) -> None:
        """Record agent finding in shared memory timeline."""
        self._findings.append({
            "agent_name": agent_name,
            "role": role,
            "finding": finding,
        })

    def get_all_findings(self) -> List[Dict[str, Any]]:
        """Return all logged agent findings."""
        return list(self._findings)

    def snapshot(self) -> Dict[str, Any]:
        """Return unified memory snapshot."""
        return {
            "topic_slug": self.topic_slug,
            "memory": dict(self._memory),
            "artifacts_count": len(self._artifacts),
            "findings_count": len(self._findings),
        }
