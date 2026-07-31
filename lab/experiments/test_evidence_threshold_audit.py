import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from lab.candidates.threshold_audit import EvidenceThresholdAuditor
from lab.candidates.real_user_evidence_ingestion import RealUserEvidenceIngestionValidator
from lab.candidates.real_user_evidence_analysis import RealUserEvidenceAnalyzer


@pytest.fixture
def auditor():
    return EvidenceThresholdAuditor()


@pytest.fixture
def validator():
    return RealUserEvidenceIngestionValidator()


@pytest.fixture
def analyzer():
    return RealUserEvidenceAnalyzer()


def test_1_ape_cannot_treat_own_threshold_as_observed_evidence(auditor):
    """1. Hardcoded threshold (10 users) is audited as PROVISIONAL_THRESHOLD, NOT customer evidence."""
    res = auditor.audit_thresholds("home_local_services", user_responses=[])
    item = res["threshold_audit"][0]
    assert item["status"] == "PROVISIONAL_THRESHOLD"
    assert item["is_empirically_justified"] is False


def test_2_ten_responses_is_not_automatically_scientifically_validated(auditor):
    """2. Threshold 10 is explicitly marked as arbitrary heuristic (is_arbitrary=True)."""
    res = auditor.audit_thresholds("home_local_services", user_responses=[])
    item = res["threshold_audit"][0]
    assert item["is_arbitrary"] is True
    assert "UNFOUNDED" in item["evidence_basis"]


def test_3_ten_responses_is_not_guaranteed_go(analyzer):
    """3. 10 responses do NOT guarantee GO if negative evidence is present."""
    responses = [
        {"response_id": f"r_{i}", "source": "reddit", "trial_interest": False, "free_text": "won't pay"}
        for i in range(10)
    ]
    res = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services"}, responses)
    assert res["decision"] == "NO-GO"


def test_4_two_strong_negative_responses_overrides_weak_positives(analyzer):
    """4. 2 strong negative responses trigger CONTRADICTED status."""
    responses = [
        {"response_id": "pos_1", "problem_frequency": "Daily", "free_text": "minor pain"},
        {"response_id": "neg_1", "free_text": "don't have problem, current tools are fine"},
        {"response_id": "neg_2", "free_text": "no problem, won't pay"},
    ]
    res = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services"}, responses)
    assert res["hypotheses"]["H1_problem_exists"]["status"] == "CONTRADICTED"


def test_5_stated_payment_intent_differentiated_from_observed_behavior(auditor):
    """5. Stated payment intent ('Would pay') weighted lower (0.3x) than observed behavior (1.0x)."""
    res = auditor.audit_thresholds("home_local_services", user_responses=[])
    matrix = res["evidence_weight_matrix"]
    stated = next(m for m in matrix if "Stated Payment" in m["signal_type"])
    observed = next(m for m in matrix if "Observed Payment" in m["signal_type"])
    assert "0.3x" in stated["weight"]
    assert "1.0x" in observed["weight"]


def test_6_stated_trial_intent_differentiated_from_observed_behavior(auditor):
    """6. Stated trial intent ('Would try') weighted lower (0.3x) than observed installation (1.0x)."""
    res = auditor.audit_thresholds("home_local_services", user_responses=[])
    matrix = res["evidence_weight_matrix"]
    stated = next(m for m in matrix if "Stated Trial" in m["signal_type"])
    observed = next(m for m in matrix if "Observed Installation" in m["signal_type"])
    assert "0.3x" in stated["weight"]
    assert "1.0x" in observed["weight"]


def test_7_duplicate_respondents_rejected_by_ingestion(validator):
    """7. Ingestion gate strictly rejects duplicate response_ids."""
    raw = [
        {"response_id": "dup_1", "free_text": "First response"},
        {"response_id": "dup_1", "free_text": "Duplicate response"},
    ]
    clean, errors = validator.validate_responses(raw)
    assert len(clean) == 1
    assert len(errors) == 1


def test_8_test_fixture_never_counts_as_real_user_response(auditor):
    """8. TEST_FIXTURE entries do NOT increment real_user_response_count when empty file used."""
    res = auditor.audit_thresholds("home_local_services", user_responses=[])
    assert res["observed_real_user_count"] == 0


def test_9_synthetic_payload_never_counts_as_real_user_response(validator):
    """9. is_synthetic=True rejected by ingestion gate."""
    raw = [{"response_id": "bot_1", "is_synthetic": True, "free_text": "Fake review"}]
    clean, errors = validator.validate_responses(raw)
    assert len(clean) == 0


def test_10_zero_responses_remains_unknown_and_waiting_for_real_users(analyzer):
    """10. 0 responses yields UNKNOWN hypotheses and VALIDATE_MORE."""
    res = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services"}, user_responses=[])
    assert res["observed_response_count"] == 0
    assert res["hypotheses"]["H1_problem_exists"]["status"] == "UNKNOWN"
    assert res["decision"] == "VALIDATE_MORE"


def test_11_unknown_fields_not_filled_with_fake_defaults(validator):
    """11. Omitted optional fields remain None / UNKNOWN."""
    raw = [{"response_id": "r1", "free_text": "Setup pain"}]
    clean, errors = validator.validate_responses(raw)
    assert clean[0]["payment_interest"] is None
    assert clean[0]["trial_interest"] is None


def test_12_previous_orion_reports_not_customer_evidence(analyzer):
    """12. Analytical content from ORION-034..042 is audited as INFERRED / UNSUPPORTED."""
    res = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services"}, user_responses=[])
    assert res["self_critique"]["pricing_29_license"] == "UNSUPPORTED"
    assert res["self_critique"]["developer_community_outreach"] == "UNSUPPORTED"
