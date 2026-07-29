from unittest.mock import patch, MagicMock
import os

def test_orchestrator_initialization():
    from ape.intelligence.scanner.orchestrator import DiscoveryOrchestrator
    
    orchestrator = DiscoveryOrchestrator(offline=True)
    assert hasattr(orchestrator, "run_segment_discovery")
    
    results = orchestrator.run_segment_discovery()
    assert isinstance(results, list)
    # Should return mock offline opportunities

@patch.dict(os.environ, {"SERPAPI_API_KEY": "MOCK_KEY"})
@patch("ape.intelligence.scanner.adapters.web_search_adapter.requests.get")
def test_orchestrator_live_budget_boundary(mock_get):
    from ape.intelligence.scanner.orchestrator import DiscoveryOrchestrator
    
    # Configure mock response
    mock_resp = MagicMock()
    mock_resp.text = '{"organic_results": [{"title": "mock jobs", "snippet": "aranıyor"}]}'
    mock_get.return_value = mock_resp

    # Ensure limit_segments correctly restricts the scan scope
    orchestrator = DiscoveryOrchestrator(offline=False, limit_segments=1)
    
    # Ensure cache is clear
    cache_path = orchestrator.web_adapter._get_cache_path("real_estate jobs")
    if os.path.exists(cache_path):
        os.remove(cache_path)

    results = orchestrator.run_segment_discovery()

    
    # We should exactly get 1 segment result
    assert len(results) == 1
    assert results[0].tags[0] == orchestrator.SEGMENTS[0]
    
    # P0/P1 backward compatibility: full 5-segment scan by default
    full_orchestrator = DiscoveryOrchestrator(offline=False)
    full_results = full_orchestrator.run_segment_discovery()
    assert len(full_results) == 5

@patch.dict(os.environ, {"SERPAPI_API_KEY": "MOCK_KEY"})
@patch("ape.intelligence.scanner.adapters.web_search_adapter.requests.get")
def test_live_request_budget_boundary(mock_get):
    from ape.intelligence.scanner.orchestrator import DiscoveryOrchestrator
    from ape.intelligence.scanner.adapters.web_search_adapter import BudgetExhaustedError
    import pytest
    import shutil

    # Configure mock response
    mock_resp = MagicMock()
    mock_resp.text = '{"organic_results": [{"title": "mock jobs", "snippet": "aranıyor"}]}'
    mock_get.return_value = mock_resp

    # Configure live verification boundary: 1 segment, 1 query, max 1 request
    orchestrator = DiscoveryOrchestrator(
        offline=False, 
        limit_segments=1,
        live_mode=True, 
        limit_queries=1, 
        max_requests=1
    )
    
    # Ensure cache is clear so that it actually triggers HTTP mock
    cache_path = orchestrator.web_adapter._get_cache_path("real_estate jobs")
    if os.path.exists(cache_path):
        os.remove(cache_path)
    
    # 1 segment -> WebSearchAdapter -> 1 query -> 1 external request -> SUCCESS
    results = orchestrator.run_segment_discovery()
    assert len(results) == 1
    
    # Verify exact HTTP request count at the real client boundary (mock_get)
    assert mock_get.call_count == 1
    assert orchestrator.web_adapter._request_count == 1
    
    # Attempting to call the adapter again should exhaust budget immediately
    # BEFORE calling requests.get
    with pytest.raises(BudgetExhaustedError):
        orchestrator.web_adapter._external_request("another query")
        
    # The actual HTTP client call count remains exactly 1
    assert mock_get.call_count == 1
    assert orchestrator.web_adapter._request_count == 1


