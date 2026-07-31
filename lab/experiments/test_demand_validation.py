import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from lab.candidates.demand_validation import DemandValidationEngine


@pytest.fixture
def engine():
    return DemandValidationEngine()


def test_empty_user_evidence_returns_validate_more(engine):
    """Empty real user responses returns VALIDATE_MORE and 40% confidence."""
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = engine.evaluate_demand("home_local_services", raw_evidence, user_responses=[])
    assert res["decision"] == "VALIDATE_MORE"
    assert res["observed_count"] == 0
    assert res["confidence"] == 40
    assert "user_response_count = 0" in res["decision_reason"]


def test_strong_real_positive_user_evidence_returns_go(engine):
    """Real user responses with >= 40% commercial intent and N>=10 returns GO."""
    user_responses = [
        {"feedback": f"User {i} confirmed pain and wants CLI alpha", "commercial_intent": i <= 5}
        for i in range(1, 11)
    ]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN", "AudienceHeuristics"]}
    res = engine.evaluate_demand("home_local_services", raw_evidence, user_responses=user_responses)
    assert res["decision"] == "GO"
    assert res["confidence"] >= 80
    assert res["observed_count"] >= 10


def test_strong_negative_user_evidence_returns_no_go(engine):
    """Real user responses with < 10% commercial intent returns NO-GO."""
    user_responses = [
        {"feedback": "No interest, current tools are fine", "commercial_intent": False}
        for _ in range(6)
    ]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = engine.evaluate_demand("home_local_services", raw_evidence, user_responses=user_responses)
    assert res["decision"] == "NO-GO"
    assert "Low customer demand" in res["decision_reason"]


def test_unsupported_pricing_drops_confidence(engine):
    """Pricing hypothesis remains UNSUPPORTED when no real payment data exists."""
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = engine.evaluate_demand("home_local_services", raw_evidence, user_responses=[])
    pricing_exp = res["validation_experiment"]["pricing_experiment"]
    assert pricing_exp["evidence_status"] == "UNSUPPORTED"
    assert "PROPOSED_THRESHOLD" in pricing_exp["proposed_success_threshold"]


def test_inferred_evidence_cannot_be_counted_as_observed(engine):
    """INFERRED != OBSERVED invariant: Inferred items do not increment observed_count."""
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = engine.evaluate_demand("home_local_services", raw_evidence, user_responses=[])
    assert res["observed_count"] == 0
    assert res["inferred_count"] == 3
    inferred_items = [e for e in res["evidence_collected"] if e["category"] in ("INFERRED", "PROPOSED_THRESHOLD")]
    assert len(inferred_items) == 3


def test_synthetic_user_evidence_rejection(engine):
    """Synthetic user responses trigger strict NO-GO rejection (SPEC-0012 invariant)."""
    user_responses = [{"feedback": "Fabricated bot review", "is_synthetic": True}]
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = engine.evaluate_demand("home_local_services", raw_evidence, user_responses=user_responses)
    assert res["decision"] == "NO-GO"
    assert res["confidence"] == 0
    assert "Synthetic" in res["decision_reason"]


def test_proposed_thresholds_not_reported_as_observed_evidence(engine):
    """Proposed targets are categorized as PROPOSED_THRESHOLD, not OBSERVED."""
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = engine.evaluate_demand("home_local_services", raw_evidence, user_responses=[])
    threshold_item = next(e for e in res["evidence_collected"] if "Proposed threshold" in e["item"])
    assert threshold_item["category"] == "PROPOSED_THRESHOLD"


def test_evidence_lineage_preservation(engine):
    """Verifies evidence lineage hash and source list are preserved intact."""
    raw_evidence = {
        "topic": "home_local_services",
        "sources": ["HackerNews", "AudienceHeuristics"],
        "evidence_hash": "sha256_demand_validation_ledger",
    }
    res = engine.evaluate_demand("home_local_services", raw_evidence, user_responses=[])
    assert res["evidence_lineage"]["evidence_hash"] == "sha256_demand_validation_ledger"
    assert res["evidence_lineage"]["sources"] == ["HackerNews", "AudienceHeuristics"]
