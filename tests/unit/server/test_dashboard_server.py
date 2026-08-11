"""
Unit tests for Observability Web Server & Dashboard Backend (PR-7A / EPIC-1).
"""

import threading
import time
import urllib.request
from pathlib import Path

from ape.server import BuildStore, run_dashboard_server


def test_build_store_listing(tmp_path: Path):
    store = BuildStore(tmp_path)
    builds = store.list_builds()
    assert isinstance(builds, list)


def test_dashboard_server_endpoints(tmp_path: Path):
    server = run_dashboard_server(tmp_path, port=9876)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.5)

    try:
        # 1. Test HTML Dashboard UI
        with urllib.request.urlopen("http://127.0.0.1:9876/") as resp:
            html = resp.read().decode("utf-8")
            assert "APE Platform — Observability Dashboard" in html
            assert "Governed AI Production Platform" in html

        # 2. Test /api/status REST endpoint
        with urllib.request.urlopen("http://127.0.0.1:9876/api/status") as resp:
            data = resp.read().decode("utf-8")
            assert "ONLINE" in data

        # 3. Test /api/builds REST endpoint
        with urllib.request.urlopen("http://127.0.0.1:9876/api/builds") as resp:
            data = resp.read().decode("utf-8")
            assert "[" in data
    finally:
        server.shutdown()
        server.server_close()
