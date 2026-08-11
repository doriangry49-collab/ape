"""
RFC-014 — Roadmap Policy Semantics Tests (S-3)

Verifies that RoadmapGenerator produces policy-appropriate milestone tracks
and that Roadmap carries the policy_decision and decision_id fields.
"""
import json
from pathlib import Path

from ape.intelligence.roadmap.engine import RoadmapGenerator

# ─────────────────────────────────────────────────────────────────────────────
# Test helpers
# ─────────────────────────────────────────────────────────────────────────────

def _write_decision_artifact(
    project_root: Path,
    slug: str,
    decision: str,
    policy: str,
    score: int = 75,
) -> Path:
    """Write a minimal decision artifact that RoadmapGenerator can read."""
    decisions_dir = project_root / ".build" / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "decision_id": f"dec_{slug}",
        "decision": decision,
        "policy": policy,
        "overall_score": score,
        "confidence": 80,
    }
    path = decisions_dir / f"{slug}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# S-3: BUILD → MVP development milestones
# ─────────────────────────────────────────────────────────────────────────────

def test_build_decision_generates_mvp_roadmap(tmp_path: Path):
    """
    RFC-014 S-3: A BUILD decision must produce an MVP development roadmap.
    Expected milestones: Design & Architecture, MVP Development, Launch & Validation.
    """
    slug = "build-topic"
    _write_decision_artifact(tmp_path, slug, decision="BUILD", policy="BUILD_NOW", score=85)

    generator = RoadmapGenerator(tmp_path)
    roadmap = generator.generate_roadmap("Build Topic", slug)

    milestone_titles = [m.title for m in roadmap.milestones]
    assert "Design & Architecture" in milestone_titles, (
        "BUILD roadmap must include 'Design & Architecture' milestone"
    )
    assert "MVP Development" in milestone_titles, (
        "BUILD roadmap must include 'MVP Development' milestone"
    )
    assert "Launch & Validation" in milestone_titles, (
        "BUILD roadmap must include 'Launch & Validation' milestone"
    )

    # Verify no VALIDATE milestones leaked in
    assert "Problem Validation" not in milestone_titles, (
        "BUILD roadmap must NOT include VALIDATE-track milestones"
    )
    assert "Signal Testing" not in milestone_titles, (
        "BUILD roadmap must NOT include VALIDATE-track milestones"
    )


# ─────────────────────────────────────────────────────────────────────────────
# S-3: VALIDATE → Market validation milestones
# ─────────────────────────────────────────────────────────────────────────────

def test_validate_decision_generates_validation_roadmap(tmp_path: Path):
    """
    RFC-014 S-3: A VALIDATE decision must produce a market validation roadmap.
    Expected milestones: Problem Validation, Signal Testing, Evidence Review.
    SPEC-0013 §3: VALIDATE means 'landing page/survey', not MVP.
    """
    slug = "validate-topic"
    _write_decision_artifact(tmp_path, slug, decision="VALIDATE", policy="VALIDATE_WITH_USERS", score=65)

    generator = RoadmapGenerator(tmp_path)
    roadmap = generator.generate_roadmap("Validate Topic", slug)

    milestone_titles = [m.title for m in roadmap.milestones]
    assert "Problem Validation" in milestone_titles, (
        "VALIDATE roadmap must include 'Problem Validation' milestone"
    )
    assert "Signal Testing" in milestone_titles, (
        "VALIDATE roadmap must include 'Signal Testing' milestone"
    )
    assert "Evidence Review" in milestone_titles, (
        "VALIDATE roadmap must include 'Evidence Review' milestone"
    )

    # Verify no BUILD milestones leaked in
    assert "MVP Development" not in milestone_titles, (
        "VALIDATE roadmap must NOT include BUILD-track milestones"
    )
    assert "Launch & Validation" not in milestone_titles, (
        "VALIDATE roadmap must NOT include BUILD-track milestones"
    )


# ─────────────────────────────────────────────────────────────────────────────
# S-3: policy_decision field is serialized correctly
# ─────────────────────────────────────────────────────────────────────────────

def test_roadmap_carries_policy_decision_field(tmp_path: Path):
    """
    RFC-014 S-3: Roadmap model and serialized JSON must carry the policy_decision
    field so ExecutionEngine can read policy semantics without re-opening the
    decision artifact.
    """
    slug = "policy-field-topic"
    _write_decision_artifact(tmp_path, slug, decision="BUILD", policy="BUILD_NOW", score=90)

    generator = RoadmapGenerator(tmp_path)
    roadmap = generator.generate_roadmap("Policy Field Topic", slug)

    # Check model
    assert roadmap.policy_decision == "BUILD", (
        "Roadmap.policy_decision must be 'BUILD' for a BUILD decision"
    )

    # Check serialized JSON
    roadmap_dict = roadmap.to_dict()
    assert "policy_decision" in roadmap_dict, (
        "Roadmap.to_dict() must include 'policy_decision'"
    )
    assert roadmap_dict["policy_decision"] == "BUILD"

    # Check persisted file
    roadmap_file = tmp_path / ".build" / "roadmaps" / f"{slug}.json"
    assert roadmap_file.exists()
    persisted = json.loads(roadmap_file.read_text(encoding="utf-8"))
    assert persisted.get("policy_decision") == "BUILD", (
        "Persisted roadmap JSON must include 'policy_decision'"
    )


def test_roadmap_carries_decision_id(tmp_path: Path):
    """
    RFC-014 S-1+S-3: Roadmap must carry the decision_id from the DecisionReport
    so ExecutionEngine can propagate it into ExecutionState without re-opening
    the decision artifact.
    """
    slug = "decision-id-topic"
    _write_decision_artifact(tmp_path, slug, decision="BUILD", policy="BUILD_NOW", score=88)

    generator = RoadmapGenerator(tmp_path)
    roadmap = generator.generate_roadmap("Decision ID Topic", slug)

    assert roadmap.decision_id == f"dec_{slug}", (
        "Roadmap.decision_id must carry the decision_id from the DecisionReport"
    )

    roadmap_dict = roadmap.to_dict()
    assert roadmap_dict["decision_id"] == f"dec_{slug}", (
        "Roadmap.to_dict() must serialize the decision_id"
    )
