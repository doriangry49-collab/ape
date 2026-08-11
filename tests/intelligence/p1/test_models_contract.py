def test_business_evidence_fields():
    # Attempt to import the newly requested BusinessEvidence
    from ape.intelligence.models import UNKNOWN, BusinessEvidence
    
    # Create an instance to verify contract
    evidence = BusinessEvidence.all_unknown()
    
    assert evidence.search_intent_observation == UNKNOWN
    assert evidence.pain_observation == UNKNOWN
    assert evidence.manual_work_observation == UNKNOWN
    assert evidence.pricing_observation == UNKNOWN
    assert evidence.entity_observation == UNKNOWN
    assert evidence.competition_observation == UNKNOWN
    assert evidence.ai_solvability == UNKNOWN
    
def test_opportunity_has_evidence_list():
    from datetime import datetime

    from ape.intelligence.models import Opportunity
    
    opp = Opportunity(
        title="Test",
        description="Test desc",
        url="test://url",
        source="test",
        score=0,
        confidence=0.0,
        published_at=datetime.now(),
        tags=[],
        is_hypothesis=True
    )
    
    assert hasattr(opp, "business_evidence")
    assert isinstance(opp.business_evidence, list)

def test_evidence_provenance_contract():
    from datetime import datetime

    from ape.intelligence.models import EvidenceProvenance
    
    prov = EvidenceProvenance(
        source_adapter="test",
        raw_observation="test",
        request_context="normalized_query",
        retrieval_timestamp=datetime.now()
    )
    
    assert prov.request_context == "normalized_query"
    assert isinstance(prov.retrieval_timestamp, datetime)
    
    # Verify no secret fields exist by default
    assert not hasattr(prov, "api_key")
    assert not hasattr(prov, "authorization")
