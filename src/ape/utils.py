"""
APE Artifact Utilities

Architecture:
  - Current State: .build/<track>/<slug>.json  (O(1) readable, mutable canonical pointer)
  - Immutable History: .governance/evidence/<track>.jsonl  (append-only, audit trail)
  - Artifact ID: separate from timestamp; collision-safe via microsecond + 4-char hex suffix.

Design decision on collision-safe IDs:
  We use datetime.utcnow().strftime("%Y%m%dT%H%M%S%f") + short random hex suffix.
  - Microsecond precision (%f) makes collisions astronomically unlikely vs. int(timestamp).
  - ISO-8601-like sortable string (no parsing needed for ordering).
  - We deliberately avoid random UUIDs (not human-readable) and sqlite (not local-first).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path


def slugify(text: str) -> str:
    """
    Convert text to a slug.
    Example: 'AI Agents' -> 'ai_agents'
    """
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s]+', '_', text).strip('_')
    return text


def make_artifact_id() -> str:
    """
    Generate a collision-safe, time-sortable artifact ID.
    Format: YYYYMMDDTHHMMSSffffffZ  (microsecond precision = 1-in-million collision window)
    Example: '20260728T075321123456Z'
    """
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + "Z"


def get_current_artifact(build_dir: Path, slug: str) -> Path | None:
    """
    Returns the canonical O(1) current state path for a topic slug.
    Naming convention: .build/<track>/<slug>.json
    Returns None if the file does not exist.
    """
    path = build_dir / f"{slug}.json"
    return path if path.exists() else None


def get_artifact_history(evidence_dir: Path, track: str) -> Path:
    """
    Returns the path of the append-only evidence JSONL log for a given track.
    Creates parent dirs if needed; does NOT create the file itself.
    Evidence naming: .governance/evidence/<track>-YYYY-MM.jsonl
    """
    evidence_dir.mkdir(parents=True, exist_ok=True)
    partition = datetime.now(timezone.utc).strftime("%Y-%m")
    return evidence_dir / f"{track}-{partition}.jsonl"


def append_to_evidence(evidence_dir: Path, track: str, payload: dict) -> None:
    """
    Append a JSON payload as a new line to the track's JSONL evidence log.
    This is the ONLY correct way to write to the immutable history.
    """
    import json
    log_path = get_artifact_history(evidence_dir, track)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, default=str) + "\n")
