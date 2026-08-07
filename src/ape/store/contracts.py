"""
Centralized State & Store Contracts — Capability M Specification.
Defines StoreRecord and BaseArtifactStore protocol interfaces for thread-safe state storage.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol, runtime_checkable


@dataclass
class StoreRecord:
    """Standardized record wrapper stored in Artifact & State Store."""
    record_id: str
    category: str  # artifact, replay_snapshot, log, evidence, workspace_state
    topic_slug: str
    data: Dict[str, Any] = field(default_factory=dict)
    checksum: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "category": self.category,
            "topic_slug": self.topic_slug,
            "data": self.data,
            "checksum": self.checksum,
            "timestamp": self.timestamp,
        }


@runtime_checkable
class BaseArtifactStore(Protocol):
    """Constitutional Protocol contract for Centralized Artifact & State Stores."""

    def put(self, record: StoreRecord) -> bool:
        """Persist a record into store."""
        ...

    def get(self, record_id: str) -> Any:
        """Retrieve record by ID."""
        ...

    def query(self, category: str, topic_slug: str) -> List[StoreRecord]:
        """Query records by category and topic slug."""
        ...
