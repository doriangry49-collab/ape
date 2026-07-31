import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from lab.candidates.real_user_evidence_ingestion import RealUserEvidenceIngestionValidator
from lab.candidates.real_user_evidence_analysis import RealUserEvidenceAnalyzer


@pytest.fixture
def validator():
    return RealUserEvidenceIngestionValidator()


@pytest.fixture
def analyzer():
    return RealUserEvidenceAnalyzer()


# =====================================================================
# 1. Ingestion Gate Contract Tests
# =====================================================================

def test_contract_1_empty_input(validator, analyzer):
    """Contract Test 1: Empty input [] passes ingestion, observed_count=0, decision=VALIDATE_MORE, GO=IMPOSSIBLE."""
    clean, errors = validator.validate_responses([])
    assert len(clean) == 0
    assert len(errors) == 0

    res = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services"}, clean)
    assert res["observed_response_count"] == 0
    assert res["decision"] == "VALIDATE_MORE"
    assert "IMPOSSIBLE" in res["decision_reason"]


def test_contract_2_synthetic_data_rejection(validator):
    """Contract Test 2: Ingestion gate strictly rejects is_synthetic=True payload."""
    raw = [{"response_id": "r1", "is_synthetic": True, "free_text": "Fake review"}]
    clean, errors = validator.validate_responses(raw)
    assert len(clean) == 0
    assert len(errors) == 1
    assert "is_synthetic=True" in errors[0]


def test_contract_3_missing_response_id_rejection(validator):
    """Contract Test 3: Ingestion gate strictly rejects payload missing response_id."""
    raw = [{"source": "reddit", "free_text": "Setup is slow"}]
    clean, errors = validator.validate_responses(raw)
    assert len(clean) == 0
    assert len(errors) == 1
    assert "missing or empty required field 'response_id'" in errors[0]


def test_contract_4_duplicate_response_id_rejection(validator):
    """Contract Test 4: Ingestion gate strictly rejects duplicate response_ids."""
    raw = [
        {"response_id": "dup_1", "free_text": "First response"},
        {"response_id": "dup_1", "free_text": "Duplicate response"},
    ]
    clean, errors = validator.validate_responses(raw)
    assert len(clean) == 1
    assert len(errors) == 1
    assert "duplicate response_id 'dup_1'" in errors[0]


def test_contract_5_pii_field_rejection(validator):
    """Contract Test 5: Ingestion gate strictly rejects forbidden PII fields."""
    for pii in ["name", "email", "phone", "address", "ip"]:
        raw = [{"response_id": "r1", pii: "user_data", "free_text": "Setup pain"}]
        clean, errors = validator.validate_responses(raw)
        assert len(clean) == 0
        assert len(errors) == 1
        assert "forbidden PII fields" in errors[0]


def test_contract_6_completely_blank_response_rejection(validator):
    """Contract Test 6: Ingestion gate strictly rejects blank records with no content."""
    raw = [{"response_id": "blank_1"}]
    clean, errors = validator.validate_responses(raw)
    assert len(clean) == 0
    assert len(errors) == 1
    assert "completely blank response record" in errors[0]


def test_contract_7_unknown_optional_fields_preservation(validator):
    """Contract Test 7: Omitted optional fields are preserved as None/UNKNOWN without fake default values."""
    raw = [{"response_id": "r1", "source": "reddit", "free_text": "Manual setup pain"}]
    clean, errors = validator.validate_responses(raw)
    assert len(clean) == 1
    assert clean[0]["problem_frequency"] is None
    assert clean[0]["trial_interest"] is None
    assert clean[0]["payment_interest"] is None


def test_contract_8_schema_valid_test_fixture_behavior(validator, analyzer):
    """Contract Test 8: Schema-valid test fixture is validated correctly (TEST FIXTURE — NOT REAL USER EVIDENCE)."""
    test_fixture = [{
        "response_id": "test_fixture_001",
        "source": "survey",
        "target_customer_match": True,
        "problem_frequency": "Daily",
        "trial_interest": True,
        "payment_interest": True,
        "free_text": "TEST FIXTURE — NOT REAL USER EVIDENCE",
    }]
    clean, errors = validator.validate_responses(test_fixture)
    assert len(clean) == 1
    assert len(errors) == 0


# =====================================================================
# 2. Decision Gate Verification Rules (A - G)
# =====================================================================

def test_rule_a_zero_responses_go_impossible(analyzer):
    """Rule A: observed_response_count == 0 => GO decision is IMPOSSIBLE."""
    res = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services"}, user_responses=[])
    assert res["decision"] == "VALIDATE_MORE"
    assert "IMPOSSIBLE" in res["decision_reason"]


def test_rule_b_unknown_hypothesis_go_impossible(analyzer):
    """Rule B: Any UNKNOWN hypothesis => GO decision is IMPOSSIBLE."""
    responses = [
        {"response_id": f"r_{i}", "source": "reddit", "problem_frequency": "Daily", "free_text": "High pain"}
        for i in range(10)
    ]
    # Payment interest is omitted -> H2 Payment is UNKNOWN
    res = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services"}, responses)
    assert res["hypotheses"]["H2_payment_intent"]["status"] == "UNKNOWN"
    assert res["decision"] == "VALIDATE_MORE"


def test_rule_c_inferred_not_observed_invariant(analyzer):
    """Rule C: INFERRED != OBSERVED - Analytical inferences cannot count as observed evidence."""
    res = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services"}, user_responses=[])
    crit = res["self_critique"]
    assert crit["pricing_29_license"] == "UNSUPPORTED"
    assert crit["developer_community_outreach"] == "UNSUPPORTED"
    assert "PROPOSED_THRESHOLD" in crit["target_50_devs_14_days"]


def test_rule_d_synthetic_response_triggers_rejection(validator, analyzer):
    """Rule D: Synthetic responses are rejected by ingestion gate and analysis engine."""
    raw = [{"response_id": "bot_1", "is_synthetic": True, "free_text": "Fake feedback"}]
    clean, errors = validator.validate_responses(raw)
    assert len(clean) == 0

    res = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services", "is_synthetic": True}, [])
    assert res["decision"] == "NO-GO"
    assert res["confidence"] == 0


def test_rule_e_invalid_responses_excluded_from_pipeline(validator):
    """Rule E: Invalid responses (PII/duplicate/blank) are excluded before reaching analysis engine."""
    raw = [
        {"response_id": "valid_1", "free_text": "Valid setup pain"},
        {"response_id": "invalid_1", "email": "test@pii.com"},
        {"response_id": "valid_1", "free_text": "Duplicate valid_1"},
    ]
    clean, errors = validator.validate_responses(raw)
    assert len(clean) == 1
    assert clean[0]["response_id"] == "valid_1"
    assert len(errors) == 2


def test_rule_f_missing_optional_fields_not_filled_with_fake_defaults(validator):
    """Rule F: Missing optional fields stay None (UNKNOWN), avoiding fake default insertion."""
    raw = [{"response_id": "r1", "free_text": "Setup pain"}]
    clean, errors = validator.validate_responses(raw)
    assert clean[0]["current_spend"] is None
    assert clean[0]["problem_frequency"] is None


def test_rule_g_empty_does_not_equal_negative_evidence(analyzer):
    """Rule G: EMPTY != NEGATIVE_EVIDENCE (0 responses = WAITING_FOR_REAL_USERS/UNKNOWN, not customer rejection)."""
    # Case 1: Empty input -> UNKNOWN / VALIDATE_MORE
    res_empty = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services"}, user_responses=[])
    assert res_empty["hypotheses"]["H1_problem_exists"]["status"] == "UNKNOWN"
    assert res_empty["decision"] == "VALIDATE_MORE"

    # Case 2: Negative input -> CONTRADICTED / NO-GO
    negative_responses = [
        {"response_id": f"neg_{i}", "source": "forum", "trial_interest": False, "free_text": "don't have problem, won't pay"}
        for i in range(5)
    ]
    res_neg = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services"}, user_responses=negative_responses)
    assert res_neg["decision"] == "NO-GO"
    assert len(res_neg["negative_evidence"]) >= 5


# =====================================================================
# 3. Self-Critique Regression Test (ORION-034 to ORION-039 Reports)
# =====================================================================

def test_self_critique_regression_past_reports_are_not_observed_evidence(analyzer):
    """Regression Test: Reports ORION-034 to ORION-039 content cannot be treated as observed real user evidence."""
    res = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services"}, user_responses=[])
    assert res["observed_response_count"] == 0
    # Hypotheses derived from ORION-034 through ORION-039 remain UNKNOWN/UNSUPPORTED
    assert res["hypotheses"]["H1_problem_exists"]["status"] == "UNKNOWN"
    assert res["hypotheses"]["H2_payment_intent"]["status"] == "UNKNOWN"
    assert res["hypotheses"]["H3_acquisition_trial_intent"]["status"] == "UNKNOWN"
