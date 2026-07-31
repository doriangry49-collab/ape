import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from lab.candidates.product_validation import ProductValidationEngine


@pytest.fixture
def engine():
    return ProductValidationEngine()


def test_strong_real_evidence_returns_go(engine):
    """Grounded real evidence with low unsupported ratio returns GO."""
    card = {
        "product_name": "Grounded Tool",
        "target_customer": ["Developers"],
        "problem": "Manual API setup is expensive and slow",
        "existing_alternatives": ["CompA", "CompB"],
    }
    raw_evidence = {
        "topic": "ai_agents",
        "pain_points": ["Manual API setup is expensive and slow"],
        "discussions": [{"title": "HN Thread 1", "points": 200}, {"title": "HN Thread 2", "points": 300}],
        "competitors": ["CompA", "CompB"],
        "target_audience": ["Software Developers"],
        "sources": ["HackerNews", "Github", "Reddit", "BBB"],
        "market_signals": ["Signal 1", "Signal 2"],
        "evidence_hash": "sha256_strong_hash",
    }
    res = engine.validate_opportunity(card, raw_evidence)
    assert res["decision"] == "GO"
    assert res["confidence"] >= 75
    assert res["evidence_quality"] >= 70


def test_insufficient_evidence_returns_validate_more(engine):
    """High heuristic score but unsupported claims & low evidence quality returns VALIDATE_MORE."""
    card = {
        "product_name": "Hypothetical Tool",
        "target_customer": ["Founders"],
        "problem": "Manual local setup overhead",
        "monetization_hypothesis": "$29 license",
        "first_customer_acquisition_hypothesis": "Show HN",
        "success_criteria": "50 active devs in 14 days",
    }
    raw_evidence = {
        "topic": "home_local_services",
        "pain_points": ["Manual local setup overhead"],
        "discussions": [],
        "competitors": [],
        "sources": ["HackerNews", "AudienceHeuristics"],
        "evidence_hash": "sha256_weak_hash",
    }
    res = engine.validate_opportunity(card, raw_evidence)
    assert res["decision"] == "VALIDATE_MORE"
    assert res["evidence_lineage"]["unsupported_claims_ratio"] >= 0.35


def test_strong_negative_signals_returns_no_go(engine):
    """Severe negative evidence signals trigger NO-GO decision."""
    card = {"product_name": "Flawed Idea"}
    raw_evidence = {
        "topic": "flawed_idea",
        "pain_points": [],
        "discussions": [],
        "competitors": [],
        "sources": [],
        "risks": ["High churn", "No buyer intent", "Legal restriction"],
        "evidence_hash": "sha256_flawed",
    }
    res = engine.validate_opportunity(card, raw_evidence)
    assert res["decision"] == "NO-GO"
    assert res["evidence_quality"] == 0


def test_high_score_low_confidence_returns_validate_more(engine):
    """High demand/pain scores with confidence < 75% returns VALIDATE_MORE."""
    card = {
        "product_name": "High Score Low Conf",
        "problem": "Manual work",
        "monetization_hypothesis": "$99/mo",
    }
    raw_evidence = {
        "topic": "unverified_high_score",
        "pain_points": ["Manual work"],
        "discussions": [{"points": 100}],
        "competitors": [],
        "target_audience": ["Developers"],
        "sources": ["SingleSource"],
    }
    res = engine.validate_opportunity(card, raw_evidence)
    assert res["decision"] == "VALIDATE_MORE"


def test_synthetic_evidence_rejection(engine):
    """Synthetic evidence flag triggers strict NO-GO rejection (SPEC-0012 invariant)."""
    card = {"product_name": "Fake Product"}
    raw_evidence = {
        "topic": "fake_topic",
        "pain_points": ["Fake pain"],
        "is_synthetic": True,
    }
    res = engine.validate_opportunity(card, raw_evidence)
    assert res["decision"] == "NO-GO"
    assert "Synthetic" in res["decision_reason"]


def test_evidence_lineage_preservation(engine):
    """Verifies evidence lineage hash and sources list are preserved intact."""
    card = {"product_name": "Lineage Check"}
    raw_evidence = {
        "topic": "lineage_topic",
        "pain_points": ["Pain A"],
        "sources": ["Source A", "Source B"],
        "evidence_hash": "sha256_exact_ledger_hash",
    }
    res = engine.validate_opportunity(card, raw_evidence)
    assert res["evidence_lineage"]["evidence_hash"] == "sha256_exact_ledger_hash"
    assert res["evidence_sources"] == ["Source A", "Source B"]
