def test_evidence_requires_provenance():
    from ape.intelligence.models import BusinessEvidence, EvidenceProvenance, UNKNOWN
    import pytest
    
    # Should raise error if provenance is missing when not using all_unknown
    with pytest.raises(TypeError):
        # Missing provenance
        BusinessEvidence(
            search_intent_observation=True,
            pain_observation=UNKNOWN,
            manual_work_observation=UNKNOWN,
            pricing_observation=UNKNOWN,
            entity_observation=UNKNOWN,
            competition_observation=UNKNOWN,
            ai_solvability=UNKNOWN,
        )
        
    # Should work with provenance
    prov = EvidenceProvenance(source_adapter="test", raw_observation="test obs")
    ev = BusinessEvidence(
        search_intent_observation=True,
        pain_observation=UNKNOWN,
        manual_work_observation=UNKNOWN,
        pricing_observation=UNKNOWN,
        entity_observation=UNKNOWN,
        competition_observation=UNKNOWN,
        ai_solvability=UNKNOWN,
        provenance=prov
    )
    assert ev.provenance == prov
    assert ev.ai_solvability == UNKNOWN
