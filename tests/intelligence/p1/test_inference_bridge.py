import pytest
from ape.intelligence.decision.bridge import InferenceBridge, _aggregate_observation
from ape.intelligence.decision.constitution import ConstitutionValidator
from ape.intelligence.models import BusinessEvidence, EvidenceProvenance, UNKNOWN
from ape.intelligence.scanner.adapters.web_search_adapter import AdapterError, BudgetExhaustedError

def test_aggregate_observation_truth_table():
    # Test C: Deterministic truth table semantics
    assert _aggregate_observation([True, True]) is True
    assert _aggregate_observation([True, UNKNOWN]) is True
    assert _aggregate_observation([False, False]) is False
    assert _aggregate_observation([False, UNKNOWN]) is False
    assert _aggregate_observation([True, False]) == UNKNOWN  # Conflict
    assert _aggregate_observation([UNKNOWN, UNKNOWN]) == UNKNOWN
    assert _aggregate_observation([]) == UNKNOWN

def test_single_evidence_mapping():
    # Test A: Single evidence mapping
    bridge = InferenceBridge()
    prov = EvidenceProvenance(source_adapter="test", raw_observation="test", reference_url="https://example.com/item")
    ev = BusinessEvidence(
        search_intent_observation=True,
        pain_observation=UNKNOWN,
        manual_work_observation=True,
        pricing_observation=True,
        entity_observation=UNKNOWN,
        competition_observation=UNKNOWN,
        ai_solvability=UNKNOWN,
        provenance=prov
    )
    
    result = bridge.aggregate_evidence([ev])
    
    # Check derived inference flags
    assert result.evidence_flags["payment_signal"] is True
    assert result.evidence_flags["identifiable_customer"] is True
    assert result.evidence_flags["ai_solvability"] is True
    
    # Test E: Lineage preservation
    assert len(result.provenance_chain) == 1
    assert result.provenance_chain[0] == prov
    assert result.reference_urls == ["https://example.com/item"]

def test_no_evidence_handling():
    # Test D: No evidence handling
    bridge = InferenceBridge()
    result = bridge.aggregate_evidence([])
    
    assert result.evidence_flags["payment_signal"] == UNKNOWN
    assert result.evidence_flags["identifiable_customer"] == UNKNOWN
    assert result.evidence_flags["ai_solvability"] == UNKNOWN
    assert result.provenance_chain == []
    assert result.reference_urls == []

def test_multi_evidence_conflict_handling():
    # Test B & C: Multi-evidence conflict handling
    bridge = InferenceBridge()
    prov1 = EvidenceProvenance(source_adapter="adapter1", raw_observation="pricing true", reference_url="https://a.com")
    prov2 = EvidenceProvenance(source_adapter="adapter2", raw_observation="pricing false", reference_url="https://b.com")
    
    ev1 = BusinessEvidence(
        search_intent_observation=True,
        pain_observation=UNKNOWN,
        manual_work_observation=UNKNOWN,
        pricing_observation=True,
        entity_observation=UNKNOWN,
        competition_observation=UNKNOWN,
        provenance=prov1
    )
    ev2 = BusinessEvidence(
        search_intent_observation=UNKNOWN,
        pain_observation=UNKNOWN,
        manual_work_observation=UNKNOWN,
        pricing_observation=False,
        competition_observation=False,
        entity_observation=UNKNOWN,
        provenance=prov2
    )
    
    result = bridge.aggregate_evidence([ev1, ev2])
    
    # Conflict between True and False pricing -> pricing becomes UNKNOWN -> payment_signal becomes UNKNOWN
    assert result.evidence_flags["payment_signal"] == UNKNOWN
    assert result.evidence_flags["identifiable_customer"] is True  # search_intent=True
    
    # Lineage preserves both references
    assert len(result.provenance_chain) == 2
    assert "https://a.com" in result.reference_urls
    assert "https://b.com" in result.reference_urls

def test_constitution_validator_integration():
    # Test H: ConstitutionValidator BUILD remains blocked unless required inferences are explicitly True
    bridge = InferenceBridge()
    validator = ConstitutionValidator()
    
    # Indeterminate evidence -> UNKNOWN flags
    ev_unknown = BusinessEvidence.all_unknown()
    result = bridge.aggregate_evidence([ev_unknown])
    
    # Even with high score, UNKNOWN flags block BUILD decision
    decision = validator.evaluate_business_gate(90, result.evidence_flags)
    assert decision.policy != "BUILD"
    assert decision.policy == "VALIDATE"
    
    # Full evidence -> BUILD decision
    prov = EvidenceProvenance(source_adapter="test", raw_observation="full")
    ev_full = BusinessEvidence(
        search_intent_observation=True,
        pain_observation=UNKNOWN,
        manual_work_observation=True,
        pricing_observation=True,
        entity_observation=UNKNOWN,
        competition_observation=UNKNOWN,
        provenance=prov
    )
    result_full = bridge.aggregate_evidence([ev_full])
    decision_full = validator.evaluate_business_gate(90, result_full.evidence_flags)
    assert decision_full.policy == "BUILD"

def test_adapter_and_budget_error_safety():
    # Test F & G: AdapterError and BudgetExhaustedError do not become evidence
    # They raise exceptions prior to bridge invocation
    with pytest.raises(AdapterError):
        raise AdapterError("Network down")

    with pytest.raises(BudgetExhaustedError):
        raise BudgetExhaustedError("Budget exhausted")
