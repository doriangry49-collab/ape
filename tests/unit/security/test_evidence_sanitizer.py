"""
Unit and E2E Tests for Evidence Sanitizer Security Boundary — ORION-158 Phase 3.
"""

import json
import pytest
from pathlib import Path
from ape.utils import (
    sanitize_evidence_payload,
    append_to_evidence,
    DENYLIST_KEYS,
    ALLOWLIST_KEYS,
)


def test_key_denylist_redaction():
    payload = {
        "api_key": "sk-test12345678901234567890",
        "client_secret": "secret_abc123456789",
        "custom_password_field": "my_password_123",
    }
    sanitized = sanitize_evidence_payload(payload)
    assert sanitized["api_key"] == "[REDACTED_DENYLIST_KEY]"
    assert sanitized["client_secret"] == "[REDACTED_DENYLIST_KEY]"
    assert sanitized["custom_password_field"] == "[REDACTED_DENYLIST_KEY]"


def test_allowlist_preservation():
    payload = {
        "provider": "openai",
        "model": "gpt-4o",
        "status": "COMPLETED",
        "token_count": 450,
        "duration_ms": 1200,
    }
    sanitized = sanitize_evidence_payload(payload)
    assert sanitized == payload


def test_pattern_regex_redaction():
    fake_bearer = "Bearer " + "X" * 20
    fake_ghp = "ghp_" + "Y" * 36
    fake_aws = "AKIA" + "Z" * 16

    payload = {
        "stdout": f"curl -H 'Authorization: {fake_bearer}' https://api.com",
        "github_log": f"Authenticating with token {fake_ghp}",
        "aws_log": f"Using key {fake_aws} for deployment",
        "url_log": "Failed GET https://api.service.com/v1?api_key=secret_param_key_99999",
        "kv_log": "secret=super_secret_value_12345",
    }
    sanitized = sanitize_evidence_payload(payload)
    assert fake_bearer not in sanitized["stdout"]
    assert "[REDACTED_BEARER_TOKEN]" in sanitized["stdout"]

    assert fake_ghp not in sanitized["github_log"]
    assert "[REDACTED_GITHUB_TOKEN]" in sanitized["github_log"]

    assert fake_aws not in sanitized["aws_log"]
    assert "[REDACTED_AWS_KEY]" in sanitized["aws_log"]

    assert "secret_param_key_99999" not in sanitized["url_log"]
    assert "[REDACTED_QUERY_PARAM]" in sanitized["url_log"]

    assert "super_secret_value_12345" not in sanitized["kv_log"]
    assert "[REDACTED_VALUE]" in sanitized["kv_log"]



def test_nested_recursion_depth_limit():
    deep_payload = {}
    curr = deep_payload
    for i in range(15):
        curr["nest"] = {}
        curr = curr["nest"]

    with pytest.raises(RecursionError, match="maximum recursion depth exceeded"):
        sanitize_evidence_payload(deep_payload, max_depth=10)


def test_fail_closed_exception_handling(tmp_path):
    deep_payload = {}
    curr = deep_payload
    for _ in range(15):
        curr["nest"] = {}
        curr = curr["nest"]

    # append_to_evidence MUST NOT raise an exception; it writes a REDACTION_FAILURE record to disk and returns normally
    append_to_evidence(tmp_path, "execution_agent", deep_payload)

    log_files = list(tmp_path.glob("execution_agent-*.jsonl"))
    assert len(log_files) == 1

    raw_disk_content = log_files[0].read_text(encoding="utf-8")
    assert "REDACTION_FAILURE" in raw_disk_content
    assert "RecursionError" in raw_disk_content
    assert "Sanitizer failed to process payload safely" in raw_disk_content


def test_raw_secret_never_reaches_evidence_file(tmp_path):
    synthetic_secret = "dummy-ACTIVE-SECRET-998877665544332211"

    payload = {
        "event": "AGENT_STEP",
        "task_id": "T-SECRET-PROOF",
        "params": {
            "command": f"curl -H 'Authorization: Bearer {synthetic_secret}' https://api.com?api_key={synthetic_secret}"
        },
        "custom_unrecognized_secret_key": synthetic_secret,
    }

    append_to_evidence(tmp_path, "execution_agent", payload)

    log_files = list(tmp_path.glob("execution_agent-*.jsonl"))
    assert len(log_files) == 1

    raw_disk_content = log_files[0].read_text(encoding="utf-8")

    # KESİN KABUL KRİTERLERİ (ASSERTIONS)
    assert synthetic_secret not in raw_disk_content, "CRITICAL: Synthetic secret string leaked into disk file!"
    assert "[REDACTED_BEARER_TOKEN]" in raw_disk_content
    assert "[REDACTED_QUERY_PARAM]" in raw_disk_content
    assert "[REDACTED_DENYLIST_KEY]" in raw_disk_content

    # JSONL format check
    log_data = json.loads(raw_disk_content.strip())
    assert log_data["event"] == "AGENT_STEP"
    assert log_data["custom_unrecognized_secret_key"] == "[REDACTED_DENYLIST_KEY]"


def test_evidence_subscriber_uses_sanitized_boundary(tmp_path):
    from ape.capabilities.governance.evidence_subscriber import GovernanceEvidenceSubscriber
    from ape.capabilities.resiliency import RuntimeEvent

    subscriber = GovernanceEvidenceSubscriber(evidence_dir=str(tmp_path))
    synthetic_secret = "dummy-SUBSCRIBER-SECRET-1122334455"

    event = RuntimeEvent(
        event_type="GovernedCapabilityStarted",
        capability_id="cap-proof",
        trace_id="tr-proof",
        provider_id="prov-proof",
        details={"api_key": synthetic_secret, "info": f"Bearer {synthetic_secret}"},
        timestamp="2026-08-19T00:00:00Z"
    )

    subscriber.handle_event(event)

    log_files = list(tmp_path.glob("decisions-*.jsonl"))
    assert len(log_files) == 1

    raw_disk_content = log_files[0].read_text(encoding="utf-8")

    assert synthetic_secret not in raw_disk_content, "CRITICAL: Synthetic secret leaked through evidence subscriber!"
    assert "[REDACTED_DENYLIST_KEY]" in raw_disk_content
    assert "[REDACTED_BEARER_TOKEN]" in raw_disk_content

