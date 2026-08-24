import json

from ape.intelligence.decision.constitution import ConstitutionValidator
from ape.intelligence.decision.engine import DecisionEngine
from ape.intelligence.decision.scorer import Scorer
from ape.utils import slugify


def test_slugify_backwards_compatibility():
    # Normal short topics remain unchanged
    assert slugify("AI Agents") == "ai_agents"
    assert slugify("   Machine Learning   ") == "machine_learning"
    assert slugify("GPT-4 & LLMs") == "gpt-4_llms"

def test_slugify_long_topic():
    # Long topic should not exceed safe length and should have hash
    long_topic = "This is a very long topic that definitely exceeds the fifty character limit we established"
    slug = slugify(long_topic)
    assert len(slug) <= 59 # 50 chars + "_" + 8 char hash = 59
    assert "_" in slug
    assert len(slug.split("_")[-1]) == 8 # hash part is 8 chars

def test_slugify_collision():
    # Topics that share the first 50 characters but differ at the end must yield different slugs
    prefix = "a" * 50
    slug1 = slugify(prefix + "b")
    slug2 = slugify(prefix + "c")
    assert slug1 != slug2
    assert slug1.startswith("a" * 50)
    assert slug2.startswith("a" * 50)

def test_slugify_determinism():
    # Same input must always produce the same slug
    long_topic = "Build a python script that does exactly what I want and nothing else 1234567890"
    slug1 = slugify(long_topic)
    slug2 = slugify(long_topic)
    assert slug1 == slug2

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


def test_decision_engine_preserves_discovery_lineage_metadata(tmp_path):
    """Verifies that DecisionEngine preserves discovery_lineage metadata without changing decision score."""
    research_dir = tmp_path / ".build" / "research"
    research_dir.mkdir(parents=True)

    mock_discovery_lineage = {
        "scan_mode": "business",
        "scanned_at": "2026-07-31T12:00:00Z",
        "source_artifact": "2026-07-31-business-scan.json",
        "opportunity_title": "Local Services App",
        "opportunity_slug": "local_services_app",
        "discovery_source": "business_scanner",
        "discovery_score": 88,
        "is_hypothesis": True,
    }

    mock_json = {
        "metadata": {
            "research_id": "res_456",
            "discovery_lineage": mock_discovery_lineage,
        },
        "confidence": 85,
        "pain_points": ["p1", "p2", "p3"],
        "discussions": ["d1"],
        "risks": [],
        "competitors": [],
        "target_audience": ["t1"],
    }

    with open(research_dir / "local_services.json", "w") as f:
        json.dump(mock_json, f)

    engine_with_lineage = DecisionEngine(tmp_path)
    report_with_lineage = engine_with_lineage.run_decision("Local Services", "local_services")

    assert "discovery_lineage" in report_with_lineage.metadata
    assert report_with_lineage.metadata["discovery_lineage"] == mock_discovery_lineage

    # Check Markdown evidence trace
    md_content = (tmp_path / ".build" / "decisions" / "local_services.md").read_text(encoding="utf-8")
    assert "Discovery Lineage" in md_content
    assert "2026-07-31-business-scan.json" in md_content

    # Lineage Neutrality Audit: Ensure score calculation is strictly identical without lineage
    mock_json_no_lineage = dict(mock_json)
    mock_json_no_lineage["metadata"] = {"research_id": "res_456"}
    with open(research_dir / "local_services_no_lineage.json", "w") as f:
        json.dump(mock_json_no_lineage, f)

    report_no_lineage = engine_with_lineage.run_decision("Local Services", "local_services_no_lineage")

    assert report_with_lineage.overall_score == report_no_lineage.overall_score
    assert report_with_lineage.confidence == report_no_lineage.confidence
    assert report_with_lineage.decision == report_no_lineage.decision
