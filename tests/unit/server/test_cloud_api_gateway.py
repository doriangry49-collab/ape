"""
Unit tests for Gen-7B Cloud API Gateway and Web SPA Endpoints.
"""

from pathlib import Path
from unittest.mock import MagicMock

from ape.server.app import APEDashboardHTTPRequestHandler


def test_cloud_api_gateway_endpoints(tmp_path: Path):
    """Test Gen-7B Cloud REST API Gateway endpoints."""
    handler = APEDashboardHTTPRequestHandler.__new__(APEDashboardHTTPRequestHandler)
    handler.store = MagicMock()
    handler.store.project_root = tmp_path

    sent_data = {}

    def mock_send_json(data, status=200):
        nonlocal sent_data
        sent_data = data

    handler._send_json = mock_send_json

    # 1. /api/v1/status
    handler.path = "/api/v1/status"
    handler.do_GET()
    assert sent_data["status"] == "ONLINE"
    assert "Operating System" in sent_data["platform"]

    # 2. /api/v1/system/health
    handler.path = "/api/v1/system/health"
    handler.do_GET()
    assert sent_data["status"] == "HEALTHY"
    assert sent_data["jwt_auth"] == "ENABLED"

    # 3. /api/v1/executive/scorecard
    handler.path = "/api/v1/executive/scorecard"
    handler.do_GET()
    assert "overall_health_score" in sent_data
