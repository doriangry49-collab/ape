"""
Thread-safe Artifact Store — Capability M Specification.
Handles persistent deliverable artifacts, replay snapshots, and build log index storage under .build/store/.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ape.store.contracts import StoreRecord


class ArtifactStore:
    """Thread-safe centralized artifact and replay snapshot store."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.store_dir = self.project_root / ".build" / "store"
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._records: Dict[str, StoreRecord] = {}
        self._load_all()

    def _load_all(self) -> None:
        index_file = self.store_dir / "index.json"
        if index_file.exists():
            try:
                data = json.loads(index_file.read_text(encoding="utf-8"))
                for rid, rdata in data.items():
                    self._records[rid] = StoreRecord(
                        record_id=rid,
                        category=rdata.get("category", "artifact"),
                        topic_slug=rdata.get("topic_slug", "default"),
                        data=dict(rdata.get("data", {})),
                        checksum=rdata.get("checksum", ""),
                        timestamp=rdata.get("timestamp", ""),
                    )
            except Exception:
                pass

    def _flush_index(self) -> None:
        index_file = self.store_dir / "index.json"
        data = {rid: rec.to_dict() for rid, rec in self._records.items()}
        index_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def put(self, category: str, topic_slug: str, data: Dict[str, Any], record_id: Optional[str] = None) -> StoreRecord:
        """Thread-safe persistence of an artifact or snapshot record."""
        with self._lock:
            rid = record_id or f"{category}_{len(self._records) + 1:04d}"
            raw_bytes = json.dumps(data, sort_keys=True).encode("utf-8")
            checksum = hashlib.sha256(raw_bytes).hexdigest()
            tstamp = time.strftime("%Y-%m-%d %H:%M:%S")

            rec = StoreRecord(
                record_id=rid,
                category=category,
                topic_slug=topic_slug,
                data=data,
                checksum=checksum,
                timestamp=tstamp,
            )
            self._records[rid] = rec

            # Persist record file
            rec_file = self.store_dir / f"{rid}.json"
            rec_file.write_text(json.dumps(rec.to_dict(), indent=2), encoding="utf-8")
            self._flush_index()
            return rec

    def get(self, record_id: str) -> Optional[StoreRecord]:
        """Fetch record by ID."""
        with self._lock:
            return self._records.get(record_id)

    def query(self, category: Optional[str] = None, topic_slug: Optional[str] = None) -> List[StoreRecord]:
        """Query records by category or topic slug."""
        with self._lock:
            results: List[StoreRecord] = []
            for rec in self._records.values():
                if category and rec.category.lower() != category.lower():
                    continue
                if topic_slug and rec.topic_slug.lower() != topic_slug.lower():
                    continue
                results.append(rec)
            return results
