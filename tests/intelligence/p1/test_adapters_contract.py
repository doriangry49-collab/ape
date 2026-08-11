def test_web_search_adapter_contract():
    from ape.intelligence.models import UNKNOWN
    from ape.intelligence.scanner.adapters.web_search_adapter import WebSearchAdapter
    
    adapter = WebSearchAdapter()
    
    # Mocking the network call
    # Job posting mock
    ev = adapter.process_mock_result("Eleman aranıyor, emlak asistanı")
    
    assert ev.manual_work_observation is True
    assert ev.pricing_observation == UNKNOWN
    assert ev.ai_solvability == UNKNOWN
    assert ev.provenance is not None

def test_complaint_adapter_contract():
    from ape.intelligence.models import UNKNOWN
    from ape.intelligence.scanner.adapters.complaint_adapter import ComplaintAdapter
    
    adapter = ComplaintAdapter()
    ev = adapter.process_mock_result("Şikayet: çok kötü hizmet")
    
    assert ev.pain_observation is True
    assert ev.ai_solvability == UNKNOWN
    assert ev.provenance is not None

def test_serpapi_malformed_json_failure():
    import pytest

    from ape.intelligence.scanner.adapters.web_search_adapter import AdapterError, WebSearchAdapter
    
    adapter = WebSearchAdapter()
    
    # TEST A, B, C: Malformed JSON triggers AdapterError, producing NO BusinessEvidence
    with pytest.raises(AdapterError):
        adapter.process_live_result("query", "invalid { json")

def test_serpapi_valid_organic_result_with_link():
    from ape.intelligence.scanner.adapters.web_search_adapter import WebSearchAdapter
    
    adapter = WebSearchAdapter()
    valid_json = '{"organic_results": [{"title": "Eleman aranıyor", "snippet": "Asistan aranıyor", "link": "https://example.com/job1"}]}'
    ev = adapter.process_live_result("real_estate jobs", valid_json)
    
    # Test A: title, snippet, link preserved and reference_url populated
    assert ev.provenance.reference_url == "https://example.com/job1"
    assert "Title: Eleman aranıyor" in ev.provenance.raw_observation
    assert "Snippet: Asistan aranıyor" in ev.provenance.raw_observation
    assert "Link: https://example.com/job1" in ev.provenance.raw_observation
    assert ev.manual_work_observation is True

def test_serpapi_valid_response_without_link():
    from ape.intelligence.scanner.adapters.web_search_adapter import WebSearchAdapter
    
    adapter = WebSearchAdapter()
    json_no_link = '{"organic_results": [{"title": "Eleman aranıyor", "snippet": "Asistan"}]}'
    ev = adapter.process_live_result("query", json_no_link)
    
    # Test B: reference_url is None when link is absent
    assert ev.provenance.reference_url is None
    assert ev.manual_work_observation is True

def test_serpapi_valid_json_undetermined_observation():
    from ape.intelligence.models import UNKNOWN
    from ape.intelligence.scanner.adapters.web_search_adapter import WebSearchAdapter
    
    adapter = WebSearchAdapter()
    
    # Test C: Valid JSON but no keywords matched -> produces UNKNOWN observations
    valid_empty_json = '{"organic_results": [{"title": "Just a normal site", "snippet": "No keywords here", "link": "https://example.com"}]}'
    ev = adapter.process_live_result("query", valid_empty_json)
    
    assert ev.manual_work_observation == UNKNOWN
    assert ev.pricing_observation == UNKNOWN
    assert ev.competition_observation == UNKNOWN
    assert ev.provenance.reference_url == "https://example.com"

def test_serpapi_malformed_json_failure():
    import pytest

    from ape.intelligence.scanner.adapters.web_search_adapter import AdapterError, WebSearchAdapter
    
    adapter = WebSearchAdapter()
    
    # Test D: Malformed JSON triggers AdapterError, producing NO BusinessEvidence
    with pytest.raises(AdapterError):
        adapter.process_live_result("query", "invalid { json")

def test_serpapi_network_failure_semantics():
    import os
    from unittest.mock import patch

    import pytest
    import requests

    from ape.intelligence.scanner.adapters.web_search_adapter import AdapterError, WebSearchAdapter
    
    adapter = WebSearchAdapter(max_requests=1)
    
    # Test E: Network/provider failure raises AdapterError, producing NO BusinessEvidence
    with patch.dict(os.environ, {"SERPAPI_API_KEY": "SECRET_KEY_123"}), \
         patch("requests.get", side_effect=requests.exceptions.ConnectionError("Connection failed")):
        with pytest.raises(AdapterError):
            adapter._external_request("unique_failing_query")

def test_serpapi_cache_hit_provenance_and_secret_safety():
    import os
    from unittest.mock import patch

    from ape.intelligence.scanner.adapters.web_search_adapter import WebSearchAdapter
    
    adapter = WebSearchAdapter(max_requests=1)
    test_query = "unique_secret_safety_query"
    
    # Clear cache for test query
    cache_path = adapter._get_cache_path(test_query)
    if os.path.exists(cache_path):
        os.remove(cache_path)

    secret_key = "SERP_SUPER_SECRET_KEY"
    valid_payload = '{"organic_results": [{"title": "Job Posting", "snippet": "aranıyor", "link": "https://example.com/job"}]}'
    
    with patch.dict(os.environ, {"SERPAPI_API_KEY": secret_key}), \
         patch("requests.get") as mock_get:
        mock_get.return_value.text = valid_payload
        mock_get.return_value.raise_for_status = lambda: None
        
        # First call: populate cache
        res_raw = adapter._external_request(test_query)
        assert mock_get.call_count == 1
        
        # Test G: Secret Safety - API key MUST NOT appear in cache file
        with open(cache_path, "r", encoding="utf-8") as f:
            cached_content = f.read()
        assert secret_key not in cached_content
        
        # Test F: Cache hit returns cached data, no second HTTP call made
        res_cached = adapter._external_request(test_query)
        assert res_cached == res_raw
        assert mock_get.call_count == 1  # Still 1, no second HTTP call
        
        # Verify evidence provenance produced from cached payload
        ev = adapter.process_live_result(test_query, res_cached)
        assert ev.provenance.reference_url == "https://example.com/job"
        assert secret_key not in ev.provenance.raw_observation


