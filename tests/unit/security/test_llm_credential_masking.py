"""
Security tests — LLM Credential Masking  (ORION-158 discipline, LLM layer).

Target code:
  src/ape/intelligence/roadmap/llm.py   — OpenAICompatibleProvider.generate()
  src/ape/intelligence/roadmap/engine.py — fallback print on planner failure

Invariant:
  A synthetic, recognisable API key MUST NEVER appear verbatim in:
  - The RuntimeError message raised by OpenAICompatibleProvider
  - The stdout print produced by RoadmapGenerator's fallback handler
  regardless of whether the underlying failure is a network error,
  an HTTPError with a body that echoes the key, or any other exception.
"""

from __future__ import annotations

import io
import sys
import urllib.error
from http.client import HTTPMessage
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from ape.intelligence.roadmap.llm import OpenAICompatibleProvider

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SYNTHETIC_KEY = "sk-SYNTHETIC_TEST_KEY_DO_NOT_USE_abc123xyz789"


def _make_provider() -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        api_key=SYNTHETIC_KEY,
        model="gpt-test",
        base_url="https://test.invalid/v1",
    )


# ---------------------------------------------------------------------------
# 1. Generic connection / timeout error — key must not appear in RuntimeError
# ---------------------------------------------------------------------------


def test_generic_exception_key_not_in_error_message():
    """
    When urlopen raises a generic exception whose str() includes the api_key
    (e.g. an odd urllib implementation that echoes the Authorization header),
    the re-raised RuntimeError must have the key redacted.
    """
    provider = _make_provider()

    # Craft an exception whose message contains the key verbatim
    evil_exc = Exception(f"Connection failed with header Bearer {SYNTHETIC_KEY} — timeout")

    with patch("urllib.request.urlopen", side_effect=evil_exc):
        with pytest.raises(RuntimeError) as exc_info:
            provider.generate("test prompt", "system", {"type": "object"})

    error_text = str(exc_info.value)
    assert SYNTHETIC_KEY not in error_text, (
        f"Raw api_key leaked in RuntimeError message: {error_text!r}"
    )
    assert "[REDACTED_API_KEY]" in error_text


# ---------------------------------------------------------------------------
# 2. HTTPError whose body echoes the key — key must not appear in RuntimeError
# ---------------------------------------------------------------------------


def test_http_error_body_key_not_in_error_message():
    """
    Some providers return the received API key inside their 401/403 error body.
    The HTTPError handler must read the body and sanitise it before raising.
    """
    provider = _make_provider()

    body_bytes = (
        f'{{"error": "invalid_api_key", "key_received": "{SYNTHETIC_KEY}"}}'
    ).encode("utf-8")

    http_err = urllib.error.HTTPError(
        url="https://test.invalid/v1/chat/completions",
        code=401,
        msg="Unauthorized",
        hdrs=HTTPMessage(),
        fp=io.BytesIO(body_bytes),
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        with pytest.raises(RuntimeError) as exc_info:
            provider.generate("test prompt", "system", {"type": "object"})

    error_text = str(exc_info.value)
    assert SYNTHETIC_KEY not in error_text, (
        f"Raw api_key leaked from HTTPError body in RuntimeError: {error_text!r}"
    )
    assert "[REDACTED_API_KEY]" in error_text


# ---------------------------------------------------------------------------
# 3. HTTPError with a body that does NOT echo the key — body preserved as-is
# ---------------------------------------------------------------------------


def test_http_error_body_without_key_preserved():
    """
    When the HTTPError body does not contain the key, the error message
    should still surface the body content (so operators can diagnose errors).
    """
    provider = _make_provider()

    body_bytes = b'{"error": "rate_limit_exceeded", "retry_after": 60}'

    http_err = urllib.error.HTTPError(
        url="https://test.invalid/v1/chat/completions",
        code=429,
        msg="Too Many Requests",
        hdrs=HTTPMessage(),
        fp=io.BytesIO(body_bytes),
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        with pytest.raises(RuntimeError) as exc_info:
            provider.generate("test prompt", "system", {"type": "object"})

    error_text = str(exc_info.value)
    # Key must not appear (it wasn't in the body anyway — double-check)
    assert SYNTHETIC_KEY not in error_text
    # Diagnostic body content must be preserved
    assert "rate_limit_exceeded" in error_text


# ---------------------------------------------------------------------------
# 4. RoadmapGenerator fallback print — key must not appear in stdout
# ---------------------------------------------------------------------------


def test_roadmap_engine_fallback_print_does_not_leak_key(tmp_path, capsys):
    """
    When the IntelligentPlanner raises an exception whose str() contains the
    api_key, the fallback print() in RoadmapGenerator must redact it before
    writing to stdout.
    """
    import json
    import uuid

    # Minimal project structure for RoadmapGenerator
    ape_dir = tmp_path / ".ape"
    ape_dir.mkdir()
    (ape_dir / "config.toml").write_text("[ape]\n", encoding="utf-8")

    decisions_dir = tmp_path / ".build" / "decisions"
    decisions_dir.mkdir(parents=True)
    decision_id = f"dec_{uuid.uuid4().hex[:8]}"
    decision_doc = {
        "topic": "test topic",
        "topic_slug": "test_topic",
        "decision": "BUILD",
        "policy": "BUILD_NOW",
        "overall_score": 70,
        "confidence": 85,
        "rationale": [],
        "next_step": "GO",
        "evidence_hash": "abc123",
        "evidence": {},
        "decision_id": decision_id,
    }
    (decisions_dir / "test_topic.json").write_text(
        json.dumps(decision_doc), encoding="utf-8"
    )

    from ape.intelligence.roadmap.engine import RoadmapGenerator

    generator = RoadmapGenerator(tmp_path)

    # Patch the instance attribute directly — config_service is set in __init__
    mock_cs = MagicMock()
    mock_cs.planner_api_key = SYNTHETIC_KEY
    mock_cs.planner_model = "gpt-test"
    mock_cs.planner_base_url = "https://test.invalid/v1"
    generator.config_service = mock_cs

    # Make IntelligentPlanner.generate_proposal raise an exception
    # whose message contains the synthetic key verbatim
    evil_exc = RuntimeError(
        f"Planner LLM API Error: HTTP 401 Unauthorized: "
        f'{{"key": "{SYNTHETIC_KEY}"}}'
    )

    with patch(
        "ape.intelligence.roadmap.engine.IntelligentPlanner.generate_proposal",
        side_effect=evil_exc,
    ):
        # Should NOT raise; falls back to deterministic templates
        roadmap = generator.generate_roadmap("test topic", "test_topic")

    captured = capsys.readouterr()
    assert SYNTHETIC_KEY not in captured.out, (
        f"Raw api_key leaked in fallback print stdout: {captured.out!r}"
    )
    # Roadmap should still be produced via deterministic fallback
    assert roadmap is not None
    assert roadmap.goal != ""
