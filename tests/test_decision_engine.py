import json

from ape.intelligence.decision.constitution import ConstitutionValidator
from ape.intelligence.decision.engine import DecisionEngine
from ape.intelligence.decision.scorer import Scorer
from ape.utils import slugify


def test_slugify():
    assert slugify("AI Agents") == "ai_agents"
    assert slugify("   Machine Learning   ") == "machine_learning"
    assert slugify("GPT-4 & LLMs") == "gpt-4_llms"

def test_scorer():
    weights = {"demand": 0.30, "feasibility": 0.30, "competition": 0.20, "revenue": 0.20}
    scorer = Scorer(weights)
    
    mock_research = {
        "pain_points": ["a", "b", "c"], # 3 * 15 = 45
        "discussions": ["x", "y"],      # 2 * 10 = 20 -> demand 65
        "risks": ["r1"],                # 100 - (1*15) = 85 -> feasibility 85
        "competitors": ["c1", "c2"],    # 100 - (2*20) = 60 -> comp 60
        "target_audience": ["t1", "t2"] # 30 + (2*15) = 60 -> rev 60
    }
    
    # Expected weighted:
    # d: int(65*0.3) = 19
    # f: int(85*0.3) = 25
    # c: int(60*0.2) = 12
    # r: int(60*0.2) = 12
    # total = 19 + 25 + 12 + 12 = 68
    
    total, vectors, rationale = scorer.score(mock_research)
    assert total == 68
    assert vectors["demand"] == 65
    assert vectors["feasibility"] == 85
    assert vectors["competition"] == 60
    assert vectors["revenue"] == 60
    assert len(rationale) == 5

def test_constitution_validator():
    validator = ConstitutionValidator()
    
    # High score -> BUILD
    dec, pol, step = validator.validate(85, {"feasibility": 50, "demand": 80})
    assert dec == "BUILD"
    assert pol == "BUILD_NOW"
    
    # Low feasibility -> IGNORE regardless of score
    dec, pol, step = validator.validate(90, {"feasibility": 10, "demand": 100})
    assert dec == "IGNORE"
    assert pol == "IGNORE"
    
    # Mid score, High demand -> BUILD
    dec, pol, step = validator.validate(65, {"feasibility": 60, "demand": 75})
    assert dec == "BUILD"
    assert pol == "BUILD_NOW"
    
    # Mid score, Low demand -> VALIDATE
    dec, pol, step = validator.validate(65, {"feasibility": 60, "demand": 60})
    assert dec == "VALIDATE"
    assert pol == "VALIDATE_WITH_USERS"
    
    # Low score -> IGNORE
    dec, pol, step = validator.validate(30, {"feasibility": 50, "demand": 30})
    assert dec == "IGNORE"

def test_decision_engine_integration(tmp_path):
    # Setup mock research file
    research_dir = tmp_path / ".build" / "research"
    research_dir.mkdir(parents=True)
    
    mock_json = {
        "metadata": {"research_id": "res_123"},
        "confidence": 85,
        "pain_points": ["p1", "p2", "p3", "p4", "p5"],
        "discussions": ["d1", "d2", "d3"],
        "risks": [],
        "competitors": [],
        "target_audience": ["t1", "t2", "t3"]
    }
    
    with open(research_dir / "ai_agents.json", "w") as f:
        json.dump(mock_json, f)
        
    engine = DecisionEngine(tmp_path)
    report = engine.run_decision("AI Agents", "ai_agents")
    
    assert report.topic == "AI Agents"
    assert report.decision == "BUILD"
    assert report.policy == "BUILD_NOW"
    assert report.overall_score > 80
    assert report.confidence == 85
    assert report.research_id == "res_123"
    assert report.evidence_hash != ""
    assert report.decision_id.startswith("dec_")
    
    # Check artifacts (canonical pointer - no timestamp in name)
    assert (tmp_path / ".build" / "decisions" / "ai_agents.json").exists()
    assert (tmp_path / ".build" / "decisions" / "ai_agents.md").exists()

    
    # Check history (append-only evidence log)
    from ape.utils import get_artifact_history
    evidence_dir = tmp_path / ".governance" / "evidence"
    history = get_artifact_history(evidence_dir, "decisions")
    assert history.exists()
    with open(history, "r") as f:
        line = f.readline()
        data = json.loads(line)
        assert data["decision"] == "BUILD"
