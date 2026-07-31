import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from lab.candidates.real_user_evidence_analysis import RealUserEvidenceAnalyzer


@pytest.fixture
def analyzer():
    return RealUserEvidenceAnalyzer()


def test_empty_input_returns_validate_more_and_go_is_impossible(analyzer):
    """1. Empty input ([] user responses) yields VALIDATE_MORE; GO is impossible and hypotheses are UNKNOWN."""
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = analyzer.analyze_evidence("home_local_services", raw_evidence, user_responses=[])
    assert res["decision"] == "VALIDATE_MORE"
    assert res["observed_response_count"] == 0
    assert res["confidence"] == 35
    assert res["hypotheses"]["H1_problem_exists"]["status"] == "UNKNOWN"
    assert res["hypotheses"]["H2_payment_intent"]["status"] == "UNKNOWN"
    assert res["hypotheses"]["H3_acquisition_trial_intent"]["status"] == "UNKNOWN"
    assert "IMPOSSIBLE" in res["decision_reason"]


def test_strong_positive_real_user_evidence_evaluates_h1_h2_h3(analyzer):
    """2. 10 positive responses confirming problem, payment, and trial intent yield GO decision."""
    user_responses = [
        {
            "response_id": f"resp_{i}",
            "source": "Reddit",
            "problem_frequency": "Daily",
            "payment_interest": True,
            "current_spend": "$30/mo",
            "trial_interest": True,
            "free_text": "Manual setup is slow and expensive",
        }
        for i in range(1, 11)
    ]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = analyzer.analyze_evidence("home_local_services", raw_evidence, user_responses)
    assert res["decision"] == "GO"
    assert res["hypotheses"]["H1_problem_exists"]["status"] == "OBSERVED"
    assert res["hypotheses"]["H2_payment_intent"]["status"] == "OBSERVED"
    assert res["hypotheses"]["H3_acquisition_trial_intent"]["status"] == "OBSERVED"
    assert res["confidence"] >= 85


def test_strong_negative_evidence_triggers_no_go(analyzer):
    """3. Strong negative user responses (>= 50% negative) yield NO-GO decision."""
    user_responses = [
        {
            "response_id": f"neg_{i}",
            "source": "Forum",
            "trial_interest": False,
            "payment_interest": False,
            "free_text": "don't have problem, current tools are fine, won't pay",
        }
        for i in range(1, 6)
    ]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = analyzer.analyze_evidence("home_local_services", raw_evidence, user_responses)
    assert res["decision"] == "NO-GO"
    assert len(res["negative_evidence"]) >= 5


def test_problem_validated_payment_unknown_returns_validate_more(analyzer):
    """4. H1=OBSERVED but H2=UNKNOWN yields VALIDATE_MORE (GO is NOT allowed)."""
    user_responses = [
        {
            "response_id": f"p_{i}",
            "source": "HN",
            "problem_frequency": "Daily",
            "free_text": "Setup is manual and broken",
            # payment_interest left omitted/unknown
        }
        for i in range(1, 5)
    ]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = analyzer.analyze_evidence("home_local_services", raw_evidence, user_responses)
    assert res["decision"] == "VALIDATE_MORE"
    assert res["hypotheses"]["H1_problem_exists"]["status"] == "OBSERVED"
    assert res["hypotheses"]["H2_payment_intent"]["status"] == "UNKNOWN"


def test_payment_negative_weakens_monetization_hypothesis(analyzer):
    """5. Explicit refusal to pay yields H2=CONTRADICTED or UNSUPPORTED."""
    user_responses = [
        {
            "response_id": "r1",
            "payment_interest": False,
            "free_text": "won't pay, too expensive, prefer free open source",
        },
        {
            "response_id": "r2",
            "payment_interest": False,
            "free_text": "no budget for local CLI",
        },
    ]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = analyzer.analyze_evidence("home_local_services", raw_evidence, user_responses)
    assert res["hypotheses"]["H2_payment_intent"]["status"] in ("CONTRADICTED", "UNSUPPORTED")
    assert res["decision"] in ("VALIDATE_MORE", "NO-GO")


def test_trial_interest_positive_problem_weak_does_not_give_go(analyzer):
    """6. H3=OBSERVED but H1=UNKNOWN/UNSUPPORTED does NOT give GO decision."""
    user_responses = [
        {
            "response_id": f"t_{i}",
            "trial_interest": True,
            # problem_frequency omitted / no pain mentioned
        }
        for i in range(1, 5)
    ]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = analyzer.analyze_evidence("home_local_services", raw_evidence, user_responses)
    assert res["decision"] == "VALIDATE_MORE"
    assert res["hypotheses"]["H1_problem_exists"]["status"] == "UNKNOWN"


def test_mixed_positive_negative_evidence_balance(analyzer):
    """7. Mixed positive and negative evidence items are categorized into positive and negative lists."""
    user_responses = [
        {"response_id": "pos1", "problem_frequency": "Daily", "trial_interest": True, "free_text": "Setup is slow"},
        {"response_id": "neg1", "payment_interest": False, "free_text": "won't pay, no budget"},
    ]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = analyzer.analyze_evidence("home_local_services", raw_evidence, user_responses)
    assert len(res["positive_evidence"]) >= 1
    assert len(res["negative_evidence"]) >= 1


def test_missing_fields_classified_as_unknown(analyzer):
    """8. Omitted fields are categorized as UNKNOWN without fabricating default values."""
    user_responses = [{"response_id": "empty_resp"}]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = analyzer.analyze_evidence("home_local_services", raw_evidence, user_responses)
    assert len(res["unknown_evidence"]) >= 1
    assert res["unknown_evidence"][0]["category"] == "UNKNOWN"


def test_inferred_hypothesis_cannot_become_observed_evidence(analyzer):
    """9. INFERRED != OBSERVED invariant: Inferred hypotheses remain UNKNOWN or UNSUPPORTED without real data."""
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = analyzer.analyze_evidence("home_local_services", raw_evidence, user_responses=[])
    crit = res["self_critique"]
    assert crit["pricing_29_license"] == "UNSUPPORTED"
    assert crit["developer_community_outreach"] == "UNSUPPORTED"
    assert "PROPOSED_THRESHOLD" in crit["target_50_devs_14_days"]


def test_synthetic_response_protection(analyzer):
    """10. Synthetic response (is_synthetic=True) triggers immediate NO-GO rejection (SPEC-0012)."""
    user_responses = [{"response_id": "fake_1", "is_synthetic": True, "free_text": "Bot feedback"}]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = analyzer.analyze_evidence("home_local_services", raw_evidence, user_responses)
    assert res["decision"] == "NO-GO"
    assert res["confidence"] == 0
    assert "Synthetic" in res["decision_reason"]
