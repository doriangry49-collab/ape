import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from lab.candidates.opportunity_challenge import OpportunityChallengeEvaluator


@pytest.fixture
def evaluator():
    return OpportunityChallengeEvaluator()


def test_challenge_evaluator_selects_winner_when_thresholds_met(evaluator):
    """Strong briefs meeting score and confidence thresholds return decision GO."""
    briefs = [
        {
            "topic": "ai_agents",
            "opportunity_score": 75,
            "confidence": 85,
            "recommended_action": "BUILD",
            "customer_pain": {"severity_score": 80, "pain_points": ["Manual setup is slow"]},
            "target_customer": {"buyers": ["AI Engineers"], "segment_type": "B2B Professional / Developer"},
            "monetization_signal": {"score": 80},
            "competitor_landscape": {"competitor_count": 2, "competition_score": 85, "incumbents": ["LangChain"]},
            "mvp_opportunity": {"feasibility_score": 70, "scope": ["CLI tool"]},
            "evidence_lineage": {"sources": ["HN"], "evidence_hash": "sha256_hash", "risk_penalty": 0},
        },
        {
            "topic": "weak_idea",
            "opportunity_score": 40,
            "confidence": 50,
            "recommended_action": "REJECT",
            "customer_pain": {"severity_score": 30, "pain_points": []},
            "target_customer": {"buyers": ["Hobbyists"], "segment_type": "Consumer"},
            "monetization_signal": {"score": 30},
            "competitor_landscape": {"competitor_count": 10, "competition_score": 20, "incumbents": []},
            "mvp_opportunity": {"feasibility_score": 40, "scope": []},
            "evidence_lineage": {"sources": [], "evidence_hash": "", "risk_penalty": 50},
        },
    ]

    res = evaluator.evaluate_candidates(briefs)
    assert res["decision"] == "GO"
    assert res["winner_topic"] == "ai_agents"
    assert res["winner_score"] > 70
    assert res["opportunity_card"] is not None
    assert res["opportunity_card"]["product_name"] == "APE Agent Gateway & Local Cache"


def test_challenge_evaluator_triggers_no_go_on_low_confidence(evaluator):
    """Brief with confidence < 70% triggers self-criticism NO-GO."""
    briefs = [
        {
            "topic": "unverified_topic",
            "opportunity_score": 80,
            "confidence": 50,  # Low confidence triggers NO-GO
            "customer_pain": {"severity_score": 70, "pain_points": ["Problem A"]},
            "target_customer": {"buyers": ["Users"], "segment_type": "Consumer"},
            "monetization_signal": {"score": 60},
            "competitor_landscape": {"competition_score": 60},
            "mvp_opportunity": {"feasibility_score": 60},
            "evidence_lineage": {"risk_penalty": 30},
        }
    ]

    res = evaluator.evaluate_candidates(briefs)
    assert res["decision"] == "NO-GO"
    assert "confidence" in res["no_go_reason"].lower()


def test_challenge_evaluator_triggers_no_go_on_empty_briefs(evaluator):
    """Empty list of briefs returns NO-GO."""
    res = evaluator.evaluate_candidates([])
    assert res["decision"] == "NO-GO"
    assert res["opportunity_card"] is None
