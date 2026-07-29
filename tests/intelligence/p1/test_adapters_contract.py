def test_web_search_adapter_contract():
    from ape.intelligence.scanner.adapters.web_search_adapter import WebSearchAdapter
    from ape.intelligence.models import UNKNOWN
    
    adapter = WebSearchAdapter()
    
    # Mocking the network call
    # Job posting mock
    ev = adapter.process_mock_result("Eleman aranıyor, emlak asistanı")
    
    assert ev.manual_work_observation is True
    assert ev.pricing_observation == UNKNOWN
    assert ev.ai_solvability == UNKNOWN
    assert ev.provenance is not None

def test_complaint_adapter_contract():
    from ape.intelligence.scanner.adapters.complaint_adapter import ComplaintAdapter
    from ape.intelligence.models import UNKNOWN
    
    adapter = ComplaintAdapter()
    ev = adapter.process_mock_result("Şikayet: çok kötü hizmet")
    
    assert ev.pain_observation is True
    assert ev.ai_solvability == UNKNOWN
    assert ev.provenance is not None

def test_serpapi_malformed_json_failure():
    from ape.intelligence.scanner.adapters.web_search_adapter import WebSearchAdapter, AdapterError
    import pytest
    
    adapter = WebSearchAdapter()
    
    # TEST A, B, C: Malformed JSON triggers AdapterError, producing NO BusinessEvidence
    with pytest.raises(AdapterError):
        adapter.process_live_result("query", "invalid { json")

def test_serpapi_valid_json_undetermined_observation():
    from ape.intelligence.scanner.adapters.web_search_adapter import WebSearchAdapter
    from ape.intelligence.models import UNKNOWN
    
    adapter = WebSearchAdapter()
    
    # TEST D: Valid JSON but no keywords matched -> produces UNKNOWN observations
    valid_empty_json = '{"organic_results": [{"title": "Just a normal site", "snippet": "No keywords here"}]}'
    ev = adapter.process_live_result("query", valid_empty_json)
    
    assert ev.manual_work_observation == UNKNOWN
    assert ev.pricing_observation == UNKNOWN
    assert ev.competition_observation == UNKNOWN

def test_serpapi_valid_json_normal_response():
    from ape.intelligence.scanner.adapters.web_search_adapter import WebSearchAdapter
    
    adapter = WebSearchAdapter()
    
    # TEST E: Valid normal SerpAPI response maps observations correctly
    valid_json = '{"organic_results": [{"title": "Eleman aranıyor", "snippet": "Fiyat teklifi için arayın"}], "ads": [{"title": "ad"}]}'
    ev = adapter.process_live_result("query", valid_json)
    
    assert ev.manual_work_observation is True
    assert ev.pricing_observation is True
    assert ev.competition_observation is True

