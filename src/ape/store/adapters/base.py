"""
Database Persistence Adapters Base Protocol — EPIC G6-1 Specification.
Defines BaseStoreAdapter protocol interface for SQLite, DuckDB, and Postgres persistence backends.
"""

from typing import List, Optional, Protocol, runtime_checkable
from ape.store.contracts import StoreRecord


@runtime_checkable
class BaseStoreAdapter(Protocol):
    """Constitutional Protocol contract for Database Store Adapters."""

    def put_record(self, record: StoreRecord) -> bool:
        """Persist a StoreRecord into relational database backend."""
        ...

    def get_record(self, record_id: str) -> Optional[StoreRecord]:
        """Fetch StoreRecord by ID."""
        ...

    def query_records(self, category: Optional[str] = None, topic_slug: Optional[str] = None) -> List[StoreRecord]:
        """Query StoreRecords by category and/or topic_slug."""
        ...
