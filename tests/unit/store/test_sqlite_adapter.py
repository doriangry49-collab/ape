"""
Unit tests for SQLiteStoreAdapter (EPIC G6-1).
"""

from pathlib import Path
import pytest

from ape.store.adapters.sqlite import SQLiteStoreAdapter
from ape.store.contracts import StoreRecord


def test_sqlite_store_adapter_crud(tmp_path: Path):
    db_file = tmp_path / "ape_store.db"
    adapter = SQLiteStoreAdapter(db_file)

    rec = StoreRecord(
        record_id="rec_001",
        category="evidence",
        topic_slug="calculator_app",
        data={"passed": True, "score": 98.5},
        checksum="sha256_mock_hash",
        timestamp="2026-08-07 14:00:00",
    )

    # 1. Put record
    assert adapter.put_record(rec) is True

    # 2. Get record
    fetched = adapter.get_record("rec_001")
    assert fetched is not None
    assert fetched.topic_slug == "calculator_app"
    assert fetched.data["score"] == 98.5

    # 3. Query record
    results = adapter.query_records(category="evidence", topic_slug="calculator_app")
    assert len(results) == 1
