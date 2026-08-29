"""Unit tests for BriefGenerator module."""

import json
from pathlib import Path
import pytest

from ape.business.brief_generator import BriefGenerator


@pytest.fixture
def sample_workspace(tmp_path: Path) -> Path:
    """Fixture providing a mock workspace with research, decision, and roadmap JSON artifacts."""
    build_dir = tmp_path / ".build"
    (build_dir / "research").mkdir(parents=True, exist_ok=True)
    (build_dir / "decisions").mkdir(parents=True, exist_ok=True)
    (build_dir / "roadmaps").mkdir(parents=True, exist_ok=True)

    topic_slug = "gebze_kocaeli_emlak_ai_sanal_staging"

    research_data = {
        "topic": "Gebze Kocaeli Emlak AI Sanal Staging",
        "confidence": 0.85,
        "target_audience": ["AI Engineers", "Product Managers"],
        "competitors": ["BoxBrownie", "OpenAI Assistants Platform"],
        "pain_points": [
            "Custom local setup required for developer integrations",
            "Lack of robust integration options reported in community threads"
        ],
        "risks": ["API rate-limiting overhead", "Token cost scaling issues"],
        "discussions": []
    }
    (build_dir / "research" / f"{topic_slug}.json").write_text(json.dumps(research_data), encoding="utf-8")

    decision_data = {
        "decision_id": "dec_64db9204",
        "evidence_hash": "398d9df6e813b6ce85eee66da1df7d6f74330fd994bbd278165d33e4a34e7a1e",
        "topic": "Gebze Kocaeli Emlak AI Sanal Staging",
        "overall_score": 48,
        "policy": "VALIDATE_WITH_USERS",
        "vector_scores": {"demand": 30, "feasibility": 55, "competition": 40, "revenue": 75},
        "rationale": ["Demand +9", "Feasibility +16", "Competition +8", "Revenue +15", "Total = 48"],
        "next_step": "Evidence present but score is borderline. Validate.",
        "provenance_chain": [
            {"source_adapter": "HackerNews", "raw_observation": "Source: HackerNews, Pain points: 1"}
        ],
        "timestamp": "2026-08-27T13:58:08.283185+00:00Z"
    }
    (build_dir / "decisions" / f"{topic_slug}.json").write_text(json.dumps(decision_data), encoding="utf-8")

    roadmap_data = {
        "roadmap_id": "rm_de34559c",
        "decision_id": "dec_64db9204",
        "policy_decision": "VALIDATE",
        "goal": "Execute VALIDATE_WITH_USERS for Gebze Kocaeli Emlak AI Sanal Staging",
        "milestones": [
            {
                "milestone_id": "ms_1",
                "title": "Problem Validation",
                "tasks": [
                    {
                        "task_id": "tsk_1_1",
                        "description": "Conduct user interviews to validate pain points",
                        "deliverables": ["docs/interview_notes.md"],
                        "estimated_effort": "3 days"
                    }
                ]
            }
        ]
    }
    (build_dir / "roadmaps" / f"{topic_slug}.json").write_text(json.dumps(roadmap_data), encoding="utf-8")

    return tmp_path


def test_brief_generator_determinism(sample_workspace: Path):
    """Verify that running generate_brief twice produces byte-identical Markdown output."""
    generator = BriefGenerator(sample_workspace)
    slug = "gebze_kocaeli_emlak_ai_sanal_staging"

    file1 = generator.generate_brief(slug)
    content1 = file1.read_text(encoding="utf-8")

    file2 = generator.generate_brief(slug)
    content2 = file2.read_text(encoding="utf-8")

    assert content1 == content2, "BriefGenerator must be 100% deterministic"


def test_brief_generator_data_integrity(sample_workspace: Path):
    """Verify that concrete data points from JSON artifacts appear accurately in the generated brief."""
    generator = BriefGenerator(sample_workspace)
    slug = "gebze_kocaeli_emlak_ai_sanal_staging"

    file_path = generator.generate_brief(slug)
    content = file_path.read_text(encoding="utf-8")

    # Data Point 1: Score 48/100
    assert "`48/100`" in content or "48/100" in content

    # Data Point 2: Competitors ("BoxBrownie")
    assert "BoxBrownie" in content

    # Data Point 3: Decision ID ("dec_64db9204")
    assert "dec_64db9204" in content

    # Data Point 4: Policy ("VALIDATE_WITH_USERS")
    assert "VALIDATE_WITH_USERS" in content

    # Data Point 5: Evidence Hash ("398d9df6e813b6ce85eee66da1df7d6f74330fd994bbd278165d33e4a34e7a1e")
    assert "398d9df6e813b6ce85eee66da1df7d6f74330fd994bbd278165d33e4a34e7a1e" in content


def test_brief_generator_fail_closed_on_missing_artifact(tmp_path: Path):
    """AC-8: Verify BriefGenerator fails closed with FileNotFoundError if any input JSON artifact is missing."""
    generator = BriefGenerator(tmp_path)
    with pytest.raises(FileNotFoundError):
        generator.generate_brief("non_existent_topic_slug")
