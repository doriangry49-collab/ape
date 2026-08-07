"""
End-to-End "Wow Moment" User Journey Test — ORION-102 Product First Specification.
Verifies the complete 5-minute browser onboarding journey:
Browser -> Workspace -> Connect GitHub Repo -> Execute Task -> Quality OS PASS -> GitHub PR created.
"""

from pathlib import Path
import pytest
from unittest.mock import MagicMock

from ape.integrations.github import GitHubWebhookHandler
from ape.server.app import APEDashboardHTTPRequestHandler


def test_wow_moment_user_journey(tmp_path: Path):
    """Verifies that a brand new user can complete the Wow Moment onboarding flow."""
    handler = APEDashboardHTTPRequestHandler.__new__(APEDashboardHTTPRequestHandler)
    handler.store = MagicMock()
    handler.store.project_root = tmp_path

    sent_data = {}

    def mock_send_json(data, status=200):
        nonlocal sent_data
        sent_data = data

    handler._send_json = mock_send_json
    handler.headers = {"Content-Length": "50"}

    # 1. Step 1: Create Workspace
    handler.path = "/api/v1/mvp/workspace"
    handler.rfile = MagicMock()
    handler.rfile.read.return_value = b'{"name": "Acme Corp"}'
    handler.do_POST()
    assert sent_data["status"] == "PROVISIONED"
    assert sent_data["slug"] == "acme_corp"

    # 2. Step 2: Connect GitHub Repository
    handler.path = "/api/v1/mvp/github/connect"
    handler.rfile.read.return_value = b'{"repo": "acme/api-service"}'
    handler.do_POST()
    assert sent_data["status"] == "CONNECTED"
    assert sent_data["repo"] == "acme/api-service"

    # 3. Step 3: Deploy AI Engineering Department Task & Receive GitHub PR
    handler.path = "/api/v1/mvp/department/run"
    handler.rfile.read.return_value = b'{"task": "Fix my REST API tests", "repo": "acme/api-service"}'
    handler.do_POST()
    assert sent_data["status"] == "RELEASED"
    assert sent_data["confidence"] == 95.5
    assert sent_data["audit"] == "PASS"
    assert "https://github.com/acme/api-service/pull/42" in sent_data["pr_url"]
