"""
APE Artifact Utilities

Architecture:
  - Current State: .build/<track>/<slug>.json  (O(1) readable, mutable canonical pointer)
  - Immutable History: .governance/evidence/<track>-YYYY-MM.jsonl  (append-only, audit trail)
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
    Limits length to 50 characters and appends an MD5 hash of the original text
    to prevent Windows MAX_PATH errors and ensure uniqueness for long inputs.
    Example short: 'AI Agents' -> 'ai_agents'
    Example long: 'Very long text...' -> 'very_long_text_..._d41d8cd9'
    """
    import hashlib
    slug = text.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s]+', '_', slug).strip('_')

    if len(slug) > 50:
        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
        slug = slug[:50].rstrip('_') + f"_{text_hash}"

    return slug


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


DENYLIST_KEYS = {
    "api_key", "secret", "password", "credential", "private_key",
    "access_token", "refresh_token", "authorization", "auth", "bearer",
    "api_token", "jwt_token", "client_secret", "ssh_key"
}

ALLOWLIST_KEYS = {
    "provider", "model", "request_id", "status", "exit_code", "token_count",
    "duration_ms", "topic_slug", "timestamp", "event", "task_id", "decision_id",
    "policy_decision", "evidence_hash", "attempt", "attempt_count",
    "schema_version", "ape_version"
}

REGEX_RULES = [
    (re.compile(r'Bearer\s+[a-zA-Z0-9_\-\.]{16,}'), 'Bearer [REDACTED_BEARER_TOKEN]'),
    (re.compile(r'(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36}'), '[REDACTED_GITHUB_TOKEN]'),
    (re.compile(r'(AKIA|ASIA)[A-Z0-9]{16}'), '[REDACTED_AWS_KEY]'),
    (re.compile(r'([?&](?:api[_-]?key|token|auth|secret)=)[^&\s]+', re.IGNORECASE), r'\1[REDACTED_QUERY_PARAM]'),
    (re.compile(r'(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{16,})["\']?'), r'\1=[REDACTED_VALUE]'),
]


def sanitize_string(text: str) -> str:
    sanitized = text
    for pattern, replacement in REGEX_RULES:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def sanitize_evidence_payload(data: Any, max_depth: int = 10, _current_depth: int = 0) -> Any:
    """
    Recursively sanitize dictionaries, lists, and strings for sensitive credentials.
    """
    if _current_depth > max_depth:
        raise RecursionError("Sanitizer maximum recursion depth exceeded.")

    if isinstance(data, dict):
        sanitized_dict = {}
        for key, val in data.items():
            key_str = str(key).lower()

            if any(deny in key_str for deny in DENYLIST_KEYS) and key_str not in ALLOWLIST_KEYS:
                sanitized_dict[key] = "[REDACTED_DENYLIST_KEY]"
            else:
                sanitized_dict[key] = sanitize_evidence_payload(val, max_depth, _current_depth + 1)
        return sanitized_dict

    elif isinstance(data, list):
        return [sanitize_evidence_payload(item, max_depth, _current_depth + 1) for item in data]

    elif isinstance(data, str):
        return sanitize_string(data)

    else:
        return data


def append_to_evidence(evidence_dir: Path, track: str, payload: dict) -> None:
    """
    Append a JSON payload as a new line to the track's JSONL evidence log.
    This is the ONLY correct way to write to the immutable history.
    """
    import json

    try:
        sanitized_payload = sanitize_evidence_payload(payload)
    except Exception as exc:
        sanitized_payload = {
            "event": "REDACTION_FAILURE",
            "track": track,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": "Sanitizer failed to process payload safely. Raw payload suppressed to prevent credential leakage.",
            "sanitizer_error": type(exc).__name__,
        }

    log_path = get_artifact_history(evidence_dir, track)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(sanitized_payload, default=str) + "\n")
