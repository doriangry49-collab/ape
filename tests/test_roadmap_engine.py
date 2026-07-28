import json

from ape.intelligence.roadmap.engine import RoadmapGenerator


def test_roadmap_generator_integration(tmp_path):
    # Setup mock decision file using canonical pointer naming
    decisions_dir = tmp_path / ".build" / "decisions"
    decisions_dir.mkdir(parents=True)

    mock_json = {
        "decision_id": "dec_123",
        "policy": "BUILD_NOW"
    }

    # Canonical pointer: no timestamp suffix
    with open(decisions_dir / "ai_agents.json", "w") as f:
        json.dump(mock_json, f)

    generator = RoadmapGenerator(tmp_path)
    roadmap = generator.generate_roadmap("AI Agents", "ai_agents")

    assert roadmap.decision_id == "dec_123"
    assert "BUILD" in roadmap.goal
    assert len(roadmap.milestones) == 3

    # Current state artifacts
    assert (tmp_path / ".build" / "roadmaps" / "ai_agents.json").exists()
    assert (tmp_path / ".build" / "roadmaps" / "ai_agents.md").exists()

    # Immutable evidence log
    from ape.utils import get_artifact_history
    evidence = get_artifact_history(tmp_path / ".governance" / "evidence", "roadmaps")
    assert evidence.exists()
    with open(evidence, "r") as f:
        data = json.loads(f.readline())
    assert data["roadmap_id"] == roadmap.roadmap_id
