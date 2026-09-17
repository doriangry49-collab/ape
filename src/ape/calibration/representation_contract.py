"""APE Representation Contract Engine (ORION G3b.3a).

Provides deterministic, target-isolated, 0–4 bounded feature representation models
(R1, R2, R3) for calibration opportunities without altering production Scorer or core pipeline.
Strictly isolated from ground truth target labels (human_expert_decision, actual_market_outcome).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple


SCHEMA_VERSION = "RepresentationContract_v1.0"

# Whitelisted input fields allowed during feature extraction
ALLOWED_INPUT_FIELDS: Set[str] = {
    "opportunity_id",
    "prompt_topic",
    "inclusion_rationale",
    "evidence_snapshots",
    "metadata",
}

# Forbidden target label fields strictly excluded from extraction
FORBIDDEN_TARGET_FIELDS: Set[str] = {
    "human_expert_decision",
    "actual_market_outcome",
    "outcome",
    "label",
    "ground_truth",
}


class TargetLeakageViolationError(ValueError):
    """Raised when a forbidden target label is accessed or passed into feature extractors."""
    pass


class RubricRangeViolationError(ValueError):
    """Raised when a feature value falls outside the mandatory [0, 4] categorical rubric bounds."""
    pass


@dataclass(frozen=True)
class RepresentationFeaturesR1:
    """R1: Current Replay Baseline (Lexical Proxy)."""
    schema_version: str
    pain_points_count: int
    discussions_count: int
    competitors_count: int
    risks_count: int


@dataclass(frozen=True)
class RepresentationFeaturesR2:
    """R2: Label-Free Semantic Features (Bounded 0–4 Rubric System)."""
    schema_version: str
    pain_evidence_depth: int          # 0..4
    user_demand_intensity: int        # 0..4
    discussion_engagement_level: int  # 0..4
    competitive_density: int          # 0..4
    risk_factors_level: int           # 0..4

    def __post_init__(self) -> None:
        """Enforce strict 0–4 range boundary invariant."""
        fields_to_check = [
            ("pain_evidence_depth", self.pain_evidence_depth),
            ("user_demand_intensity", self.user_demand_intensity),
            ("discussion_engagement_level", self.discussion_engagement_level),
            ("competitive_density", self.competitive_density),
            ("risk_factors_level", self.risk_factors_level),
        ]
        for name, val in fields_to_check:
            if not isinstance(val, int) or not (0 <= val <= 4):
                raise RubricRangeViolationError(
                    f"Feature '{name}' value {val} violates [0, 4] rubric bound!"
                )


@dataclass(frozen=True)
class RepresentationFeaturesR3:
    """R3: Oracle-Free Normalized Quality Representation."""
    schema_version: str
    normalized_evidence_density: float  # 0.0 .. 1.0
    source_authority_index: float       # 0.0 .. 1.0
    market_friction_index: float        # 0.0 .. 1.0


def filter_payload_whitelist(record: Dict[str, Any]) -> Dict[str, Any]:
    """Strips forbidden target label keys before feature extraction (Static Isolation)."""
    clean_payload: Dict[str, Any] = {}
    for k, v in record.items():
        if k in FORBIDDEN_TARGET_FIELDS:
            continue
        if k in ALLOWED_INPUT_FIELDS:
            clean_payload[k] = v
    return clean_payload


def extract_representation_r1(record: Dict[str, Any]) -> RepresentationFeaturesR1:
    """Extracts R1 Lexical Proxy Representation."""
    clean_record = filter_payload_whitelist(record)
    evidence_list = clean_record.get("evidence_snapshots", [])
    prompt_topic = clean_record.get("prompt_topic", "").lower()

    pain_points_count = sum(
        1 for ev in evidence_list
        if "pain point" in ev.get("raw_observation", "").lower() or "pain" in ev.get("raw_observation", "").lower()
    )
    discussions_count = sum(
        1 for ev in evidence_list
        if "discussion" in ev.get("raw_observation", "").lower() or "comments" in ev.get("raw_observation", "").lower()
    )
    competitors_count = 1 if "competitor" in prompt_topic or "alternative" in prompt_topic else 0
    risks_count = 3 if "hardware" in prompt_topic or "robot" in prompt_topic else 2

    return RepresentationFeaturesR1(
        schema_version=SCHEMA_VERSION,
        pain_points_count=pain_points_count,
        discussions_count=discussions_count,
        competitors_count=competitors_count,
        risks_count=risks_count,
    )


def extract_representation_r2(record: Dict[str, Any]) -> RepresentationFeaturesR2:
    """Extracts R2 Label-Free Semantic Features with 0–4 Bounded Rubric System."""
    clean_record = filter_payload_whitelist(record)
    evidence_list = clean_record.get("evidence_snapshots", [])
    prompt_topic = clean_record.get("prompt_topic", "").lower()
    inclusion_rationale = clean_record.get("inclusion_rationale", "").lower()

    # 1. Pain Evidence Depth (0-4)
    pain_obs_count = sum(
        1 for ev in evidence_list
        if any(term in ev.get("raw_observation", "").lower() for term in ["pain", "problem", "frustration", "issue", "blocker"])
    )
    if pain_obs_count == 0:
        pain_depth = 0
    elif pain_obs_count == 1:
        pain_depth = 1
    elif pain_obs_count == 2:
        pain_depth = 2
    elif pain_obs_count <= 4:
        pain_depth = 3
    else:
        pain_depth = 4

    # 2. User Demand Intensity (0-4)
    demand_obs_count = sum(
        1 for ev in evidence_list
        if any(term in ev.get("raw_observation", "").lower() for term in ["demand", "request", "need", "looking for", "buy", "pay", "order"])
    )
    if demand_obs_count == 0:
        demand_intensity = 0
    elif demand_obs_count == 1:
        demand_intensity = 1
    elif demand_obs_count == 2:
        demand_intensity = 2
    elif demand_obs_count <= 4:
        demand_intensity = 3
    else:
        demand_intensity = 4

    # 3. Discussion Engagement Level (0-4)
    disc_obs_count = sum(
        1 for ev in evidence_list
        if any(term in ev.get("raw_observation", "").lower() for term in ["discussion", "comment", "thread", "forum", "feedback"])
    )
    if disc_obs_count == 0:
        disc_level = 0
    elif disc_obs_count == 1:
        disc_level = 1
    elif disc_obs_count <= 3:
        disc_level = 2
    elif disc_obs_count <= 6:
        disc_level = 3
    else:
        disc_level = 4

    # 4. Competitive Density (0-4)
    comp_obs_count = sum(
        1 for ev in evidence_list
        if any(term in ev.get("raw_observation", "").lower() for term in ["competitor", "alternative", "vs", "rival"])
    )
    if "crowded" in inclusion_rationale or comp_obs_count >= 5:
        comp_density = 4
    elif comp_obs_count >= 3:
        comp_density = 3
    elif comp_obs_count >= 1 or "competitor" in prompt_topic:
        comp_density = 2
    elif "alternative" in prompt_topic:
        comp_density = 1
    else:
        comp_density = 0

    # 5. Risk Factors Level (0-4)
    if "hardware" in prompt_topic or "robot" in prompt_topic:
        risk_level = 4
    elif "ai" in prompt_topic or "llm" in prompt_topic:
        risk_level = 2
    else:
        risk_level = 1

    return RepresentationFeaturesR2(
        schema_version=SCHEMA_VERSION,
        pain_evidence_depth=pain_depth,
        user_demand_intensity=demand_intensity,
        discussion_engagement_level=disc_level,
        competitive_density=comp_density,
        risk_factors_level=risk_level,
    )


def extract_representation_r3(record: Dict[str, Any]) -> RepresentationFeaturesR3:
    """Extracts R3 Oracle-Free Normalized Quality Representation."""
    clean_record = filter_payload_whitelist(record)
    evidence_list = clean_record.get("evidence_snapshots", [])

    total_evidence = len(evidence_list)
    density = min(total_evidence / 10.0, 1.0)

    # Authority: GitHub/HN = 0.8+, general web = 0.5
    authority_scores = []
    for ev in evidence_list:
        src = ev.get("source", "").lower()
        if "github" in src or "hackernews" in src:
            authority_scores.append(0.9)
        else:
            authority_scores.append(0.5)

    avg_authority = sum(authority_scores) / len(authority_scores) if authority_scores else 0.0
    friction = 0.3 if total_evidence > 0 else 0.0

    return RepresentationFeaturesR3(
        schema_version=SCHEMA_VERSION,
        normalized_evidence_density=round(density, 4),
        source_authority_index=round(avg_authority, 4),
        market_friction_index=round(friction, 4),
    )
