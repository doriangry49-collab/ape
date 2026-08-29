"""Integration unit tests for BriefGenerator (G4/G6 Executive Brief deliverable assembly)."""

import json
from pathlib import Path
from ape.business.brief_generator import BriefGenerator


def test_brief_generator_with_wait_for_signal_warning_banner(tmp_path: Path):
    """Verifies BriefGenerator correctly renders warning banner and NO EXECUTIVE ACTION for WAIT_FOR_SIGNAL."""
    build_dir = tmp_path / ".build"
    (build_dir / "research").mkdir(parents=True)
    (build_dir / "decisions").mkdir(parents=True)

    slug = "gebze_kocaeli_emlak_ai_sanal_staging"
    research_file = build_dir / "research" / f"{slug}.json"
    decision_file = build_dir / "decisions" / f"{slug}.json"

    research_file.write_text(json.dumps({
        "topic": "Gebze Kocaeli Emlak AI Sanal Staging",
        "competitors": [],
        "pain_points": [],
        "target_audience": [],
        "risks": ["INSUFFICIENT_DOMAIN_EVIDENCE"],
        "confidence": 0.0,
    }), encoding="utf-8")

    decision_file.write_text(json.dumps({
        "topic": "Gebze Kocaeli Emlak AI Sanal Staging",
        "decision_id": "DEC-TEST-001",
        "evidence_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "policy": "WAIT_FOR_SIGNAL",
        "overall_score": 0,
        "vector_scores": {"demand": 0, "feasibility": 0, "competition": 0, "revenue": 0},
        "rationale": ["Zero domain evidence found on public networks."],
        "provenance_chain": [],
    }), encoding="utf-8")

    generator = BriefGenerator(tmp_path)
    output_path = generator.generate_brief(slug)

    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "Policy Decision:** `WAIT_FOR_SIGNAL`" in content
    assert "POLICY DECISION: WAIT_FOR_SIGNAL (Halted Fail-Closed / Audit Only)" in content
    assert "NO EXECUTIVE ACTION (Halted Fail-Closed)" in content


def test_brief_generator_positive_case_with_roadmap(tmp_path: Path):
    """Verifies BriefGenerator renders full Executive Brief when positive evidence and roadmap exist."""
    build_dir = tmp_path / ".build"
    (build_dir / "research").mkdir(parents=True)
    (build_dir / "decisions").mkdir(parents=True)
    (build_dir / "roadmaps").mkdir(parents=True)

    slug = "developer_documentation_search_ai_assistant"
    research_file = build_dir / "research" / f"{slug}.json"
    decision_file = build_dir / "decisions" / f"{slug}.json"
    roadmap_file = build_dir / "roadmaps" / f"{slug}.json"

    research_file.write_text(json.dumps({
        "topic": "Developer Documentation Search AI Assistant",
        "competitors": ["Mintlify", "Kapa.ai", "GrepPT"],
        "pain_points": ["Outdated documentation", "Context drift"],
        "target_audience": ["Software Engineers", "DevRel Leaders"],
        "risks": ["API rate limits"],
        "confidence": 0.85,
    }), encoding="utf-8")

    decision_file.write_text(json.dumps({
        "topic": "Developer Documentation Search AI Assistant",
        "decision_id": "DEC-TEST-002",
        "evidence_hash": "a1b2c3d4e5f67890",
        "policy": "VALIDATE_WITH_USERS",
        "overall_score": 78,
        "vector_scores": {"demand": 80, "feasibility": 85, "competition": 70, "revenue": 75},
        "rationale": ["Strong user demand and high feasibility."],
        "provenance_chain": [
            {"source_adapter": "HackerNewsAdapter", "raw_observation": "High query frequency for doc search"}
        ],
    }), encoding="utf-8")

    roadmap_file.write_text(json.dumps({
        "milestones": [
            {
                "title": "v0.1 Minimal Indexing Engine",
                "tasks": [
                    {
                        "description": "Implement doc scraper",
                        "estimated_effort": "2 days",
                        "deliverables": ["scraper.py"]
                    }
                ]
            }
        ]
    }), encoding="utf-8")

    generator = BriefGenerator(tmp_path)
    output_path = generator.generate_brief(slug)

    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "Policy Decision:** `VALIDATE_WITH_USERS`" in content
    assert "Mintlify" in content
    assert "HackerNewsAdapter" in content
    assert "v0.1 Minimal Indexing Engine" in content
