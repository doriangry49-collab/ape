import json
import pytest
from pathlib import Path
from ape.intelligence.decision.bridge import BridgeResult, InferenceBridge
from ape.intelligence.decision.constitution import ConstitutionValidator
from ape.intelligence.decision.engine import DecisionEngine
from ape.intelligence.decision.models import DecisionReport, PolicyDecision, PolicyGateResult
from ape.intelligence.roadmap.engine import RoadmapGenerator
from ape.intelligence.models import BusinessEvidence, EvidenceProvenance, UNKNOWN


def test_policy_decision_enum_properties():
    assert PolicyDecision.BUILD == "BUILD"
    assert PolicyDecision.VALIDATE == "VALIDATE"
    assert PolicyDecision.WATCH == "WATCH"
    assert PolicyDecision.IGNORE == "IGNORE"
    assert PolicyDecision.BLOCKED == "BLOCKED"
    assert str(PolicyDecision.BUILD) == "BUILD"


def test_constitution_evaluate_policy_feasibility_hard_stop():
    validator = ConstitutionValidator()
    result = validator.evaluate_policy(
        overall_score=95,
        vector_scores={"feasibility": 10, "demand": 90},
    )
    assert result.decision == PolicyDecision.IGNORE
    assert result.rule_id == "RULE_FEASIBILITY_HARD_STOP"


def test_constitution_evaluate_policy_unknown_flags_block_build():
    validator = ConstitutionValidator()
    bridge_result = BridgeResult(
        evidence_flags={
            "payment_signal": UNKNOWN,
            "identifiable_customer": True,
            "ai_solvability": True,
        }
    )

    # High score (90), but payment_signal is UNKNOWN -> MUST demote to VALIDATE
    res_high = validator.evaluate_policy(90, {"feasibility": 80}, bridge_result=bridge_result)
    assert res_high.decision == PolicyDecision.VALIDATE
    assert res_high.rule_id == "RULE_EVIDENCE_GATE_MISSING_EVIDENCE"

    # Moderate score (50), payment_signal is UNKNOWN -> MUST demote to WATCH
    res_mod = validator.evaluate_policy(50, {"feasibility": 80}, bridge_result=bridge_result)
    assert res_mod.decision == PolicyDecision.WATCH
    assert res_mod.rule_id == "RULE_EVIDENCE_GATE_BORDERLINE_SCORE"

    # Low score (30), payment_signal is UNKNOWN -> IGNORE
    res_low = validator.evaluate_policy(30, {"feasibility": 80}, bridge_result=bridge_result)
    assert res_low.decision == PolicyDecision.IGNORE
    assert res_low.rule_id == "RULE_EVIDENCE_GATE_LOW_SCORE"


def test_constitution_evaluate_policy_verified_evidence_build():
    validator = ConstitutionValidator()
    bridge_result = BridgeResult(
        evidence_flags={
            "payment_signal": True,
            "identifiable_customer": True,
            "ai_solvability": True,
        }
    )

    # High score + verified evidence -> BUILD
    res_build = validator.evaluate_policy(75, {"feasibility": 80}, bridge_result=bridge_result)
    assert res_build.decision == PolicyDecision.BUILD
    assert res_build.rule_id == "RULE_GO_BUILD_APPROVED"

    # Borderline score + verified evidence -> VALIDATE
    res_val = validator.evaluate_policy(50, {"feasibility": 80}, bridge_result=bridge_result)
    assert res_val.decision == PolicyDecision.VALIDATE
    assert res_val.rule_id == "RULE_GO_VALIDATE_BORDERLINE"


def test_decision_engine_lineage_and_provenance_preservation(tmp_path: Path):
    # Setup test workspace
    build_dir = tmp_path / ".build" / "research"
    build_dir.mkdir(parents=True, exist_ok=True)

    prov = EvidenceProvenance(
        source_adapter="test_adapter",
        raw_observation="pricing available",
        reference_url="https://example.com/pricing",
    )
    ev = BusinessEvidence(
        search_intent_observation=True,
        pain_observation=True,
        manual_work_observation=True,
        pricing_observation=True,
        entity_observation=True,
        competition_observation=True,
        provenance=prov,
    )

    research_data = {
        "topic": "SaaS Billing",
        "confidence": 85,
        "pain_points": ["p1", "p2", "p3", "p4"],
        "discussions": ["d1", "d2"],
        "target_audience": ["t1", "t2"],
        "metadata": {"research_id": "res_12345"},
        "business_evidence": [
            {
                "search_intent_observation": True,
                "pain_observation": True,
                "manual_work_observation": True,
                "pricing_observation": True,
                "entity_observation": True,
                "competition_observation": True,
                "provenance": {
                    "source_adapter": "test_adapter",
                    "raw_observation": "pricing available",
                    "reference_url": "https://example.com/pricing",
                },
            }
        ],
    }

    research_file = build_dir / "saas-billing.json"
    research_file.write_text(json.dumps(research_data), encoding="utf-8")

    engine = DecisionEngine(tmp_path)
    report = engine.run_decision("SaaS Billing", "saas-billing")

    assert isinstance(report.decision, PolicyDecision) or report.decision == PolicyDecision.BUILD
    assert report.reference_urls == ["https://example.com/pricing"]
    assert report.evidence_flags["payment_signal"] is True
    assert len(report.provenance_chain) == 1

    # Verify saved artifact
    saved_path = tmp_path / ".build" / "decisions" / "saas-billing.json"
    assert saved_path.exists()
    saved_json = json.loads(saved_path.read_text(encoding="utf-8"))
    assert saved_json["decision"] == "BUILD"
    assert saved_json["reference_urls"] == ["https://example.com/pricing"]


def test_roadmap_generator_policy_gate_enforcement(tmp_path: Path):
    decisions_dir = tmp_path / ".build" / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)

    # 1. WATCH decision artifact -> should raise ValueError
    watch_decision = {
        "decision_id": "dec_watch",
        "decision": "WATCH",
        "policy": "WAIT_FOR_SIGNAL",
    }
    (decisions_dir / "watch-topic.json").write_text(json.dumps(watch_decision), encoding="utf-8")

    generator = RoadmapGenerator(tmp_path)
    with pytest.raises(ValueError, match="Cannot generate roadmap for policy decision: WATCH"):
        generator.generate_roadmap("Watch Topic", "watch-topic")

    # 2. BUILD decision artifact -> should succeed
    build_decision = {
        "decision_id": "dec_build",
        "decision": "BUILD",
        "policy": "BUILD_NOW",
    }
    (decisions_dir / "build-topic.json").write_text(json.dumps(build_decision), encoding="utf-8")

    roadmap = generator.generate_roadmap("Build Topic", "build-topic")
    assert roadmap.decision_id == "dec_build"


# ─────────────────────────────────────────────────────────────────────────────
# RFC-013 REGRESSION — WN-1: evaluate_business_gate feasibility bypass
# ─────────────────────────────────────────────────────────────────────────────

def test_regression_wn1_business_gate_feasibility_veto_not_bypassed():
    """
    WN-1 regression: evaluate_business_gate() MUST respect the constitutional
    feasibility hard-stop when a real vector_scores dict is supplied.
    Passing feasibility=10 with an otherwise-high overall_score (90) MUST
    still yield IGNORE — not BUILD.
    Before the fix this returned BUILD (feasibility defaulted to 100).
    """
    validator = ConstitutionValidator()
    evidence_flags = {
        "payment_signal": True,
        "identifiable_customer": True,
        "ai_solvability": True,
    }

    # Without vector_scores (old default behavior) — feasibility defaults to 100 → BUILD
    result_no_scores = validator.evaluate_business_gate(
        overall_score=90,
        evidence_flags=evidence_flags,
        # vector_scores omitted on purpose — feasibility should default to 100
    )
    # With default (no vector_scores), feasibility = 100 → score 90 → BUILD is valid
    assert result_no_scores.policy == "BUILD", (
        "Without vector_scores, feasibility defaults to 100 and high score should BUILD"
    )

    # With explicit low feasibility — constitutional veto MUST fire → IGNORE
    result_low_feasibility = validator.evaluate_business_gate(
        overall_score=90,
        evidence_flags=evidence_flags,
        vector_scores={"feasibility": 10},
    )
    assert result_low_feasibility.policy == "IGNORE", (
        "Low feasibility (10 < 20) MUST trigger constitutional IGNORE "
        "regardless of overall_score or evidence_flags"
    )


def test_regression_wn1_business_gate_borderline_feasibility_passes():
    """
    WN-1 regression (boundary): feasibility == 20 should NOT trigger the hard-stop.
    The threshold is strictly < 20.
    """
    validator = ConstitutionValidator()
    evidence_flags = {
        "payment_signal": True,
        "identifiable_customer": True,
        "ai_solvability": True,
    }
    result = validator.evaluate_business_gate(
        overall_score=80,
        evidence_flags=evidence_flags,
        vector_scores={"feasibility": 20},
    )
    # feasibility == 20 is NOT < 20 → should NOT be IGNORE
    assert result.policy != "IGNORE", (
        "feasibility == 20 must NOT trigger the hard-stop (threshold is strictly < 20)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# RFC-013 REGRESSION — WN-2: evidence_flags override path provenance loss
# ─────────────────────────────────────────────────────────────────────────────

def test_regression_wn2_override_path_preserves_explicit_provenance(tmp_path: Path):
    """
    WN-2 regression: When DecisionEngine receives research_data with only
    evidence_flags (no business_evidence list), the resulting DecisionReport
    MUST have a non-empty provenance_chain — not silently [].
    Before the fix provenance_chain was always [] on this code path.
    """
    build_dir = tmp_path / ".build" / "research"
    build_dir.mkdir(parents=True, exist_ok=True)

    research_data = {
        "topic": "Override Topic",
        "confidence": 70,
        "pain_points": ["p1", "p2", "p3"],
        "discussions": ["d1"],
        "target_audience": ["ta1"],
        "metadata": {"research_id": "res_override_test"},
        # No business_evidence — pure override path
        "evidence_flags": {
            "payment_signal": True,
            "identifiable_customer": True,
            "ai_solvability": True,
        },
    }

    research_file = build_dir / "override-topic.json"
    research_file.write_text(json.dumps(research_data), encoding="utf-8")

    engine = DecisionEngine(tmp_path)
    report = engine.run_decision("Override Topic", "override-topic")

    # WN-2: provenance_chain MUST NOT be empty on override path
    assert len(report.provenance_chain) > 0, (
        "Override path MUST produce at least one synthetic provenance record "
        "(SPEC-0013 §5 audit lineage)"
    )
    # The synthetic record must identify the override origin
    first_prov = report.provenance_chain[0]
    assert first_prov.source_adapter == "evidence_flags_override", (
        "Synthetic provenance source_adapter must be 'evidence_flags_override'"
    )
    assert "evidence_flags_override" in first_prov.request_context, (
        "Synthetic provenance must identify the override request context"
    )


def test_regression_wn2_override_path_preserves_reference_urls(tmp_path: Path):
    """
    WN-2 regression: reference_urls provided alongside an evidence_flags override
    MUST survive into the DecisionReport (not be silently dropped).
    """
    build_dir = tmp_path / ".build" / "research"
    build_dir.mkdir(parents=True, exist_ok=True)

    research_data = {
        "topic": "URL Override Topic",
        "confidence": 70,
        "pain_points": ["p1", "p2", "p3"],
        "discussions": ["d1"],
        "target_audience": ["ta1"],
        "metadata": {"research_id": "res_url_override_test"},
        "evidence_flags": {
            "payment_signal": True,
            "identifiable_customer": True,
            "ai_solvability": True,
        },
        # reference_urls provided directly in research_data alongside override
        "reference_urls": ["https://example.com/market-report"],
    }

    research_file = build_dir / "url-override-topic.json"
    research_file.write_text(json.dumps(research_data), encoding="utf-8")

    engine = DecisionEngine(tmp_path)
    report = engine.run_decision("URL Override Topic", "url-override-topic")

    assert report.reference_urls == ["https://example.com/market-report"], (
        "reference_urls supplied alongside evidence_flags override must appear in DecisionReport"
    )
