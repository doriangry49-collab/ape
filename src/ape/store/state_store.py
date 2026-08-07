"""
Centralized State Store & Workspace Indexer — Capability M Specification.
Provides unified state indexing across workspace builds, evidence logs, and execution states.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ape.store.artifact_store import ArtifactStore


class StateStore:
    """Unified state store wrapper accessing ArtifactStore and workspace metadata."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.artifact_store = ArtifactStore(self.project_root)

    def record_build_state(self, topic_slug: str, execution_id: str, status: str, metadata: Dict[str, Any]) -> str:
        """Record build state snapshot into Centralized State Store."""
        rec = self.artifact_store.put(
            category="build_state",
            topic_slug=topic_slug,
            data={
                "execution_id": execution_id,
                "status": status,
                "metadata": metadata,
            },
        )
        return rec.record_id

    def get_build_state(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve build state snapshot."""
        rec = self.artifact_store.get(record_id)
        return rec.data if rec else None

    def list_recent_states(self, topic_slug: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query recent build states."""
        records = self.artifact_store.query(category="build_state", topic_slug=topic_slug)
        return [r.to_dict() for r in records]
