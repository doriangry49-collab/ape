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
# Scenario A — EMPTY
# =====================================================================
def test_scenario_a_empty(validator, analyzer):
    """Scenario A: 0 responses -> UNKNOWN hypotheses, VALIDATE_MORE, GO IMPOSSIBLE."""
    clean, errors = validator.validate_responses([])
    res = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services"}, clean)
    assert res["observed_response_count"] == 0
    assert res["hypotheses"]["H1_problem_exists"]["status"] == "UNKNOWN"
    assert res["hypotheses"]["H2_payment_intent"]["status"] == "UNKNOWN"
    assert res["hypotheses"]["H3_acquisition_trial_intent"]["status"] == "UNKNOWN"
    assert res["decision"] == "VALIDATE_MORE"
    assert "IMPOSSIBLE" in res["decision_reason"]


# =====================================================================
# Scenario B — STRONG POSITIVE (TEST FIXTURE — NOT REAL USER EVIDENCE)
# =====================================================================
def test_scenario_b_strong_positive(validator, analyzer):
    """Scenario B: 10 test fixture responses with high pain, spend, and trial intent -> GO."""
    fixture = [
        {
            "response_id": f"sim_pos_{i}",
            "source": "survey",
            "problem_frequency": "Daily",
            "payment_interest": True,
            "current_spend": "$30/mo",
            "trial_interest": True,
            "free_text": "TEST FIXTURE — NOT REAL USER EVIDENCE: Setup is manual and slow",
        }
        for i in range(1, 11)
    ]
    clean, errors = validator.validate_responses(fixture)
    assert len(clean) == 10
    res = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services"}, clean)
    assert res["hypotheses"]["H1_problem_exists"]["status"] == "OBSERVED"
    assert res["hypotheses"]["H2_payment_intent"]["status"] == "OBSERVED"
    assert res["hypotheses"]["H3_acquisition_trial_intent"]["status"] == "OBSERVED"
    assert res["decision"] == "GO"


# =====================================================================
# Scenario C — STRONG NEGATIVE (TEST FIXTURE — NOT REAL USER EVIDENCE)
# =====================================================================
def test_scenario_c_strong_negative(validator, analyzer):
    """Scenario C: 5 negative test fixture responses -> NO-GO decision."""
    fixture = [
        {
            "response_id": f"sim_neg_{i}",
            "source": "forum",
            "trial_interest": False,
            "payment_interest": False,
            "free_text": "TEST FIXTURE — NOT REAL USER EVIDENCE: don't have problem, won't pay",
        }
        for i in range(1, 6)
    ]
    clean, errors = validator.validate_responses(fixture)
    res = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services"}, clean)
    assert len(res["negative_evidence"]) >= 5
    assert res["decision"] == "NO-GO"


# =====================================================================
# Scenario D — MIXED SIGNALS (TEST FIXTURE — NOT REAL USER EVIDENCE)
# =====================================================================
def test_scenario_d_mixed_signals(validator, analyzer):
    """Scenario D: H1 positive, H2 omitted (UNKNOWN), H3 negative -> GO IMPOSSIBLE, VALIDATE_MORE or NO-GO."""
    fixture = [
        {"response_id": f"pos_{i}", "problem_frequency": "Daily", "free_text": "TEST FIXTURE: setup pain"}
        for i in range(1, 5)
    ] + [
        {"response_id": f"neg_{i}", "trial_interest": False, "free_text": "TEST FIXTURE: no interest in CLI"}
        for i in range(1, 4)
    ]
    clean, errors = validator.validate_responses(fixture)
    res = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services"}, clean)
    assert res["hypotheses"]["H2_payment_intent"]["status"] == "UNKNOWN"
    assert res["decision"] in ("VALIDATE_MORE", "NO-GO")
    assert res["decision"] != "GO"


# =====================================================================
# Scenario E — PARTIAL RESPONSES (TEST FIXTURE — NOT REAL USER EVIDENCE)
# =====================================================================
def test_scenario_e_partial_responses(validator, analyzer):
    """Scenario E: Omitted optional fields remain UNKNOWN without inserting fake defaults."""
    fixture = [
        {
            "response_id": "sim_part_1",
            "problem_frequency": "Daily",
            "free_text": "TEST FIXTURE: setup pain",
            # payment_interest, trial_interest omitted
        }
    ]
    clean, errors = validator.validate_responses(fixture)
    assert clean[0]["payment_interest"] is None
    res = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services"}, clean)
    assert res["hypotheses"]["H2_payment_intent"]["status"] == "UNKNOWN"


# =====================================================================
# Scenario F — SYNTHETIC PAYLOAD (TEST FIXTURE — NOT REAL USER EVIDENCE)
# =====================================================================
def test_scenario_f_synthetic_payload(validator, analyzer):
    """Scenario F: is_synthetic=True is rejected by ingestion validator and evaluation engine."""
    fixture = [
        {
            "response_id": "sim_bot_1",
            "is_synthetic": True,
            "free_text": "TEST FIXTURE — NOT REAL USER EVIDENCE: Fake bot feedback",
        }
    ]
    clean, errors = validator.validate_responses(fixture)
    assert len(clean) == 0
    assert len(errors) == 1
    assert "is_synthetic=True" in errors[0]

    res = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services", "is_synthetic": True}, [])
    assert res["decision"] == "NO-GO"
    assert res["confidence"] == 0


# =====================================================================
# Scenario G — SELF-GENERATED EVIDENCE ATTACK
# =====================================================================
def test_scenario_g_self_generated_evidence_attack(validator, analyzer):
    """Scenario G: Analytical quotes from prior ORION-034..039 reports are strictly classified as INFERRED/UNSUPPORTED."""
    raw_evidence = {
        "topic": "home_local_services",
        "pain_points": [
            "High API pricing and pricing model complexity ($29 license target)",
            "50 active developers in 14 days target",
            "Direct community forum outreach target"
        ],
        "sources": ["ORION-034 Report", "ORION-035 Report"]
    }
    # No real user responses ingested
    res = analyzer.analyze_evidence("home_local_services", raw_evidence, user_responses=[])
    assert res["observed_response_count"] == 0
    assert res["hypotheses"]["H1_problem_exists"]["status"] == "UNKNOWN"
    assert res["hypotheses"]["H2_payment_intent"]["status"] == "UNKNOWN"
    assert res["decision"] == "VALIDATE_MORE"
    assert res["self_critique"]["pricing_29_license"] == "UNSUPPORTED"
