import urllib.error

import pytest

from ape.intelligence.engine import OpportunityEngine
from ape.intelligence.scanner.adapters.web_search_adapter import AdapterError
from ape.intelligence.scanner.github import GitHubTrendingScanner
from ape.intelligence.scanner.hackernews import HackerNewsScanner
from ape.project import Project


def test_hackernews_scanner_raises_adapter_error_on_network_failure(monkeypatch):
    """Assert HackerNewsScanner raises AdapterError and produces no synthetic mock evidence on failure."""
    def mock_urlopen(*args, **kwargs):
        raise urllib.error.URLError("Network unreachable test")

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    scanner = HackerNewsScanner()
    with pytest.raises(AdapterError) as exc_info:
        scanner.scan()

    assert "HackerNews scan failed" in str(exc_info.value)


def test_github_trending_scanner_raises_adapter_error_on_network_failure(monkeypatch):
    """Assert GitHubTrendingScanner raises AdapterError and produces no synthetic mock evidence on failure."""
    def mock_urlopen(*args, **kwargs):
        raise urllib.error.URLError("Network unreachable test")

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    scanner = GitHubTrendingScanner()
    with pytest.raises(AdapterError) as exc_info:
        scanner.scan()

    assert "GitHub Trending scan failed" in str(exc_info.value)


def test_opportunity_engine_handles_adapter_error_gracefully(tmp_path, monkeypatch):
    """Assert OpportunityEngine gracefully catches scanner AdapterErrors and returns clean results."""
    def mock_urlopen(*args, **kwargs):
        raise urllib.error.URLError("Network offline")

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    project = Project.load(tmp_path)
    engine = OpportunityEngine(project)

    results = engine.run_scans()
    # Engine must return a list without raising uncaught exceptions
    assert isinstance(results, list)
    assert len(results) == 0
