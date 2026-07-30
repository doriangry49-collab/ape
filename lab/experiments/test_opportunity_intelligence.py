import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from lab.candidates.opportunity_intelligence import ExperimentalOpportunityScorer


@pytest.fixture
def scorer():
    return ExperimentalOpportunityScorer()


def test_strong_opportunity_evaluates_to_build(scorer):
    """Strong pain severity, high signals, B2B intent, low comp -> BUILD."""
    data = {
        "pain_points": ["Manual data entry is slow and broken", "Expensive API costs", "Waste of time"],
        "discussions": [{"title": "Show HN", "points": 500}],
        "competitors": ["Generic Tool A"],
        "target_audience": ["Software Developers", "B2B Founders"],
        "market_signals": ["High demand thread"],
        "risks": ["Minor setup risk"],
        "sources": ["HackerNews", "BBB"],
    }
    result = scorer.evaluate_opportunity(data)
    assert result["recommendation"] == "BUILD"
    assert result["experimental_score"] >= 75
    assert result["dimensions"]["customer_pain"] >= 70
    assert result["dimensions"]["monetization_potential"] >= 70


def test_weak_opportunity_evaluates_to_watch_or_reject(scorer):
    """High competition, weak signals, no budget keywords -> WATCH/REJECT."""
    data = {
        "pain_points": ["Minor annoyance"],
        "discussions": [],
        "competitors": ["Comp1", "Comp2", "Comp3", "Comp4", "Comp5", "Comp6"],
        "target_audience": ["Hobbyists"],
        "market_signals": [],
        "risks": ["High churn", "No budget", "Complex legal"],
        "sources": ["Forum"],
    }
    result = scorer.evaluate_opportunity(data)
    assert result["recommendation"] in ("WATCH", "REJECT")
    assert result["experimental_score"] < 60


def test_high_interest_low_monetization(scorer):
    """High viral points but no B2B or pricing keywords -> lower monetization score."""
    data = {
        "pain_points": ["Fun open source game glitch"],
        "discussions": [{"title": "Viral Game Post", "points": 2000}],
        "competitors": ["Game A", "Game B"],
        "target_audience": ["Casual Gamers"],
        "market_signals": ["Viral reddit post"],
        "risks": ["No monetization model"],
        "sources": ["Reddit", "HN"],
    }
    result = scorer.evaluate_opportunity(data)
    # High market signal, but low monetization
    assert result["dimensions"]["market_signal"] >= 65
    assert result["dimensions"]["monetization_potential"] < 55


def test_high_pain_high_competition(scorer):
    """High pain, but crowded red ocean competition -> low competition gap score."""
    data = {
        "pain_points": ["Manual invoice processing is slow and expensive", "Costly manual entry"],
        "discussions": [{"points": 100}],
        "competitors": ["SAP", "Oracle", "Quickbooks", "Xero", "Freshbooks", "Bill.com"],
        "target_audience": ["Accountants"],
        "market_signals": ["Market demand"],
        "risks": ["High competition risk"],
        "sources": ["HN"],
    }
    result = scorer.evaluate_opportunity(data)
    assert result["dimensions"]["customer_pain"] >= 70
    assert result["dimensions"]["competition_gap"] == 30


def test_insufficient_evidence_triggers_reject_recommendation(scorer):
    """Empty pain points and single source -> high risk penalty, REJECT recommendation."""
    data = {
        "pain_points": [],
        "discussions": [],
        "competitors": [],
        "target_audience": [],
        "market_signals": [],
        "risks": [],
        "sources": ["SingleBlog"],
    }
    result = scorer.evaluate_opportunity(data)
    assert result["recommendation"] == "REJECT"
    assert result["dimensions"]["risk_uncertainty_penalty"] >= 40


def test_generate_product_opportunity_brief_contains_all_10_sections(scorer):
    """Assert generate_product_opportunity_brief output contains all 10 key decision sections."""
    data = {
        "topic": "ai_agents",
        "pain_points": ["Manual API integration is expensive and slow"],
        "discussions": [{"title": "HN Thread", "points": 150}],
        "competitors": ["LangChain"],
        "target_audience": ["AI Engineers"],
        "market_signals": ["High velocity"],
        "risks": ["Minor risk"],
        "sources": ["HackerNews"],
        "confidence": 0.85,
    }
    brief = scorer.generate_product_opportunity_brief(data, evidence_hash="abc123sha")
    
    assert brief["topic"] == "ai_agents"
    assert brief["opportunity_score"] >= 50
    assert brief["confidence"] == 85
    assert brief["recommended_action"] in ("BUILD", "VALIDATE", "WATCH", "REJECT")
    assert "severity_score" in brief["customer_pain"]
    assert "buyers" in brief["target_customer"]
    assert "score" in brief["monetization_signal"]
    assert "competitor_count" in brief["competitor_landscape"]
    assert "Open Niche Gap" in brief["identified_gap"] or "Competition" in brief["identified_gap"]
    assert "scope" in brief["mvp_opportunity"]
    assert brief["evidence_lineage"]["evidence_hash"] == "abc123sha"
    assert "Active discussion velocity" in brief["why_now"]
