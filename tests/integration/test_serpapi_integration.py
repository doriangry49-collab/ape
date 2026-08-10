import os

import pytest

from ape.intelligence.scanner.adapters.web_search_adapter import (
    AdapterError,
    BudgetExhaustedError,
    WebSearchAdapter,
)

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

from unittest.mock import patch


def test_missing_api_key_raises_error():
    # If key is missing, verify clean failure (AdapterError)
    adapter = WebSearchAdapter(max_requests=1)
    # Ensure cache is clear so it attempts external request
    cache_path = adapter._get_cache_path("real_estate jobs")
    if os.path.exists(cache_path):
        os.remove(cache_path)

    with patch.dict(os.environ, {}, clear=True), patch("winreg.QueryValueEx", side_effect=FileNotFoundError):
        # Should raise AdapterError, not BudgetExhaustedError or network errors
        with pytest.raises(AdapterError) as exc_info:
            adapter.scan_segment("real_estate")
        assert "SERPAPI_API_KEY environment variable is not configured" in str(exc_info.value)

@pytest.mark.skipif(not os.environ.get("SERPAPI_API_KEY"), reason="SERPAPI_API_KEY environment variable is not set")
def test_serpapi_live_integration():
    import shutil
    adapter = WebSearchAdapter(max_requests=1, limit_queries=1)
    # Clear cache directory to force live request budget enforcement
    if os.path.exists(adapter.cache_dir):
        shutil.rmtree(adapter.cache_dir)

    results = adapter.scan_segment("real_estate")
    # Verify results are produced
    assert len(results) == 1
    evidence = results[0]
    assert evidence.provenance.source_adapter == "serpapi_web_search"
    assert evidence.provenance.request_context == "real_estate jobs"
    
    # Try second request -> should raise BudgetExhaustedError
    with pytest.raises(BudgetExhaustedError):
        adapter._external_request("real_estate pricing")



@pytest.mark.skipif(not os.environ.get("SERPAPI_API_KEY"), reason="SERPAPI_API_KEY environment variable is not set")
def test_serpapi_cache_behavior():
    adapter = WebSearchAdapter(max_requests=2)
    # Clear cache for this query first
    cache_path = adapter._get_cache_path("real_estate caching test")
    if os.path.exists(cache_path):
        os.remove(cache_path)
        
    # First call: hits SerpAPI and caches it
    res1 = adapter._external_request("real_estate caching test")
    assert os.path.exists(cache_path)
    
    # Reset count to test if cache bypasses budget and HTTP
    adapter._request_count = 0
    adapter.max_requests = 1
    
    # Second call: hits cache, doesn't increment count or trigger HTTP limit
    res2 = adapter._external_request("real_estate caching test")
    assert res1 == res2
    assert adapter._request_count == 0
