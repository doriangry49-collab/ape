"""
SQLite Database Store Adapter — EPIC G6-1 Specification.
Provides thread-safe relational SQLite persistence for StoreRecord entries under .build/ape_store.db.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, List, Optional

from ape.store.contracts import StoreRecord


class SQLiteStoreAdapter:
    """Thread-safe SQLite database adapter for Centralized State & Store."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with self._lock, sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS store_records (
                    record_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    topic_slug TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.commit()

    def put_record(self, record: StoreRecord) -> bool:
        """Persist StoreRecord into SQLite database."""
        with self._lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO store_records (record_id, category, topic_slug, data_json, checksum, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.record_id,
                    record.category,
                    record.topic_slug,
                    json.dumps(record.data),
                    record.checksum,
                    record.timestamp,
                ),
            )
            conn.commit()
            return True

    def get_record(self, record_id: str) -> Optional[StoreRecord]:
        """Fetch StoreRecord by ID from SQLite database."""
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT record_id, category, topic_slug, data_json, checksum, timestamp FROM store_records WHERE record_id = ?",
                (record_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return StoreRecord(
                record_id=row[0],
                category=row[1],
                topic_slug=row[2],
                data=json.loads(row[3]),
                checksum=row[4],
                timestamp=row[5],
            )

    def query_records(self, category: Optional[str] = None, topic_slug: Optional[str] = None) -> List[StoreRecord]:
        """Query StoreRecords with optional category and topic_slug filters."""
        query = "SELECT record_id, category, topic_slug, data_json, checksum, timestamp FROM store_records WHERE 1=1"
        params: List[Any] = []

        if category:
            query += " AND LOWER(category) = LOWER(?)"
            params.append(category)
        if topic_slug:
            query += " AND LOWER(topic_slug) = LOWER(?)"
            params.append(topic_slug)

        with self._lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [
                StoreRecord(
                    record_id=row[0],
                    category=row[1],
                    topic_slug=row[2],
                    data=json.loads(row[3]),
                    checksum=row[4],
                    timestamp=row[5],
                )
                for row in rows
            ]
