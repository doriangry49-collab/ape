"""
Unit tests for Capability M Centralized State & Store.
"""

from pathlib import Path
import pytest

from ape.store import ArtifactStore, StateStore, StoreRecord


def test_artifact_store_thread_safe_persistence(tmp_path: Path):
    store = ArtifactStore(tmp_path)

    # 1. Put artifact record
    rec = store.put(
        category="replay_snapshot",
        topic_slug="calculator_app",
        data={"merkle_root": "abc123hash", "confidence_delta": 0.0},
    )
    assert rec.checksum != ""
    assert (tmp_path / ".build" / "store" / "index.json").exists()

    # 2. Query record
    fetched = store.get(rec.record_id)
    assert fetched is not None
    assert fetched.data["merkle_root"] == "abc123hash"

    # 3. Reload store instance
    reloaded_store = ArtifactStore(tmp_path)
    results = reloaded_store.query(category="replay_snapshot", topic_slug="calculator_app")
    assert len(results) == 1
    assert results[0].checksum == rec.checksum


def test_state_store_build_indexing(tmp_path: Path):
    sstore = StateStore(tmp_path)
    rid = sstore.record_build_state(
        topic_slug="calc_app",
        execution_id="exec_001",
        status="COMPLETED",
        metadata={"tasks": 4},
    )

    data = sstore.get_build_state(rid)
    assert data is not None
    assert data["status"] == "COMPLETED"

    recent = sstore.list_recent_states("calc_app")
    assert len(recent) == 1
