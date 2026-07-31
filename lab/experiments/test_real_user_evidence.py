import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from lab.candidates.real_user_evidence import RealUserEvidenceEvaluator


@pytest.fixture
def evaluator():
    return RealUserEvidenceEvaluator()


def test_empty_response_set_returns_validate_more(evaluator):
    """1. Empty response set returns VALIDATE_MORE with 40% confidence and WAITING_FOR_REAL_USERS status."""
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = evaluator.evaluate_real_user_evidence("home_local_services", raw_evidence, user_responses=[])
    assert res["decision"] == "VALIDATE_MORE"
    assert res["real_responses_observed_count"] == 0
    assert res["status"] == "WAITING_FOR_REAL_USERS"
    assert res["confidence"] == 40


def test_observed_positive_responses_detected(evaluator):
    """2. Real user responses with problem frequency & trial intent detect positive evidence."""
    user_responses = [
        {
            "response_id": "r1",
            "source": "Reddit",
            "problem_frequency": "Daily",
            "trial_interest": True,
            "free_text": "Setup is slow and manual",
        }
    ]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = evaluator.evaluate_real_user_evidence("home_local_services", raw_evidence, user_responses)
    assert len(res["positive_evidence"]) >= 1
    assert res["problem_confirmation_count"] == 1
    assert res["trial_intent_count"] == 1


def test_observed_negative_responses_detected(evaluator):
    """3. User responses refusing trial or declaring no problem detect negative evidence."""
    user_responses = [
        {
            "response_id": "r1",
            "source": "Forum",
            "trial_interest": False,
            "payment_interest": False,
            "free_text": "don't have problem, current tools are fine",
        }
    ]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = evaluator.evaluate_real_user_evidence("home_local_services", raw_evidence, user_responses)
    assert len(res["negative_evidence"]) >= 1
    assert "Negative signal" in res["negative_evidence"][0]


def test_payment_intent_correctly_classified(evaluator):
    """4. Payment interest or spend text correctly increments payment_intent_count."""
    user_responses = [
        {"response_id": "r1", "payment_interest": True, "current_spend": "$30/mo"},
        {"response_id": "r2", "payment_interest": False, "current_spend": "Free"},
    ]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = evaluator.evaluate_real_user_evidence("home_local_services", raw_evidence, user_responses)
    assert res["payment_intent_count"] == 1


def test_trial_intent_correctly_classified(evaluator):
    """5. Trial opt-in correctly increments trial_intent_count."""
    user_responses = [
        {"response_id": "r1", "trial_interest": True},
        {"response_id": "r2", "trial_interest": True},
        {"response_id": "r3", "trial_interest": False},
    ]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = evaluator.evaluate_real_user_evidence("home_local_services", raw_evidence, user_responses)
    assert res["trial_intent_count"] == 2


def test_inferred_data_cannot_become_observed_evidence(evaluator):
    """6. INFERRED != OBSERVED invariant: Inferred hypotheses cannot increase observed_count."""
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = evaluator.evaluate_real_user_evidence("home_local_services", raw_evidence, user_responses=[])
    assert res["observed_count"] == 0
    assert res["inferred_count"] == 3


def test_synthetic_fake_response_rejected(evaluator):
    """7. Synthetic response (is_synthetic: True) triggers strict NO-GO rejection (SPEC-0012)."""
    user_responses = [{"response_id": "bot_1", "is_synthetic": True, "free_text": "Fake review"}]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = evaluator.evaluate_real_user_evidence("home_local_services", raw_evidence, user_responses)
    assert res["decision"] == "NO-GO"
    assert res["confidence"] == 0
    assert "Synthetic" in res["decision_reason"]


def test_mixed_positive_negative_evidence_handled(evaluator):
    """8. Mixed positive and negative responses are both recorded in their respective categories."""
    user_responses = [
        {"response_id": "pos_1", "trial_interest": True, "free_text": "Need automation"},
        {"response_id": "neg_1", "trial_interest": False, "free_text": "don't have problem"},
    ]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = evaluator.evaluate_real_user_evidence("home_local_services", raw_evidence, user_responses)
    assert len(res["positive_evidence"]) >= 1
    assert len(res["negative_evidence"]) >= 1


def test_insufficient_evidence_returns_validate_more(evaluator):
    """9. Sample size < 10 returns VALIDATE_MORE even if positive signals exist."""
    user_responses = [
        {"response_id": f"r_{i}", "payment_interest": True, "trial_interest": True}
        for i in range(3)
    ]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = evaluator.evaluate_real_user_evidence("home_local_services", raw_evidence, user_responses)
    assert res["decision"] == "VALIDATE_MORE"
    assert "Sample size insufficient" in res["decision_reason"]


def test_strong_negative_evidence_returns_no_go(evaluator):
    """10. High negative response ratio (>= 50%) returns NO-GO decision."""
    user_responses = [
        {"response_id": f"neg_{i}", "trial_interest": False, "free_text": "won't pay, current tools are fine"}
        for i in range(5)
    ]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = evaluator.evaluate_real_user_evidence("home_local_services", raw_evidence, user_responses)
    assert res["decision"] == "NO-GO"
    assert "negative evidence" in res["decision_reason"].lower()


def test_evidence_lineage_preserved(evaluator):
    """11. Evidence lineage SHA-256 hash and sources list are preserved intact."""
    raw_evidence = {
        "topic": "home_local_services",
        "sources": ["HackerNews", "AudienceHeuristics"],
        "evidence_hash": "sha256_exact_real_user_hash",
    }
    res = evaluator.evaluate_real_user_evidence("home_local_services", raw_evidence, user_responses=[])
    assert res["evidence_lineage"]["evidence_hash"] == "sha256_exact_real_user_hash"
    assert res["evidence_lineage"]["sources"] == ["HackerNews", "AudienceHeuristics"]


def test_pii_fields_not_required_for_validation(evaluator):
    """12. Anonymous schema without PII (no name/email/phone) evaluates cleanly."""
    anonymous_response = {
        "response_id": "resp_anon_99",
        "source": "Reddit r/IndieHackers",
        "target_customer_match": True,
        "problem_frequency": "Daily",
        "trial_interest": True,
        "payment_interest": True,
        "free_text": "Local CLI tool is essential",
    }
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = evaluator.evaluate_real_user_evidence("home_local_services", raw_evidence, [anonymous_response])
    assert res["real_responses_observed_count"] == 1
    assert res["target_customer_fit_count"] == 1
    assert "email" not in str(anonymous_response).lower()
    assert "name" not in str(anonymous_response).lower()
