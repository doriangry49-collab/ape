"""
HTTPTransport Abstraction Layer — ORION-112 Specification.
Defines HTTPRequest, HTTPResponse, HTTPTransport Protocol, and MockHTTPTransport for offline testing.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol, runtime_checkable


@dataclass(frozen=True)
class HTTPRequest:
    """Standardized HTTP request packet."""
    url: str
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    json_data: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 60.0


@dataclass(frozen=True)
class HTTPResponse:
    """Standardized HTTP response packet."""
    status_code: int = 200
    body_json: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300


@runtime_checkable
class HTTPTransport(Protocol):
    """Canonical HTTP Transport Protocol interface."""

    def send(self, request: HTTPRequest) -> HTTPResponse:
        ...


class MockHTTPTransport:
    """Built-in MockHTTPTransport for deterministic offline execution testing without live network calls."""

    def __init__(self, default_response: Optional[Dict[str, Any]] = None) -> None:
        self.default_response = default_response or {}
        self.last_request: Optional[HTTPRequest] = None

    def send(self, request: HTTPRequest) -> HTTPResponse:
        self.last_request = request
        if self.default_response:
            return HTTPResponse(status_code=200, body_json=dict(self.default_response))

        # Dynamic mock response based on requested payload
        raw_prompt = request.json_data.get("messages", [{}])[-1].get("content", "") if "messages" in request.json_data else ""
        text_payload = f"[TRANSPORT MOCK RESPONSE] Received request for URL {request.url}."

        return HTTPResponse(
            status_code=200,
            body_json={
                "response_text": text_payload,
                "content": [{"text": text_payload}],
                "choices": [{"message": {"content": text_payload}, "finish_reason": "stop"}],
                "candidates": [{"content": {"parts": [{"text": text_payload}]}}],
                "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
            },
        )
