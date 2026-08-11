"""
Unit tests for ORION-101 MVP Web Application & Endpoints.
"""

from pathlib import Path
from unittest.mock import MagicMock

from ape.server.app import APEDashboardHTTPRequestHandler
from ape.server.auth_web import WebAuthSessionManager


def test_web_auth_session_manager():
    mgr = WebAuthSessionManager(secret="test_secret")
    token = mgr.authenticate("demo_user", "hash123")

    assert token is not None
    assert mgr.verify_session(token) is True
    assert mgr.verify_session("invalid_token") is False


def test_mvp_web_endpoints(tmp_path: Path):
    handler = APEDashboardHTTPRequestHandler.__new__(APEDashboardHTTPRequestHandler)
    handler.store = MagicMock()
    handler.store.project_root = tmp_path

    sent_data = {}

    def mock_send_json(data, status=200):
        nonlocal sent_data
        sent_data = data

    handler._send_json = mock_send_json
    handler.headers = {"Content-Length": "30"}

    # 1. /api/v1/mvp/workspace POST
    handler.path = "/api/v1/mvp/workspace"
    handler.rfile = MagicMock()
    handler.rfile.read.return_value = b'{"name": "Acme Corp"}'
    handler.do_POST()
    assert sent_data["status"] == "PROVISIONED"
    assert sent_data["slug"] == "acme_corp"

    # 2. /api/v1/mvp/department/run POST
    handler.path = "/api/v1/mvp/department/run"
    handler.rfile.read.return_value = b'{"task": "Build REST API"}'
    handler.do_POST()
    assert sent_data["status"] == "RELEASED"
    assert sent_data["confidence"] == 95.5
    assert "merkle_proof" in sent_data
