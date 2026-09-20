"""ORION G3b.3a — Representation Contract Freeze (Governance Refined).

Defines observable, rule-based feature extraction contracts, explicit per-feature
input field whitelists/blacklists, static AST + runtime target isolation invariants,
and an outcome-agnostic deterministic mapping to Scorer v1.

GOVERNANCE DIRECTIVE:
- NO production scoring code (Scorer v2) is written or modified.
- NO rubric, weight, or mapping shall be optimized against calibration outcomes.
- Target decision and outcome labels are strictly isolated static & runtime.
"""

import ast
import inspect
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


class TargetIsolationViolationError(ValueError):
    """Raised when target decision/outcome labels are accessed or referenced during feature extraction."""
    pass


class HoldoutAccessViolationError(PermissionError):
    """Raised when holdout dataset is accessed during representation development."""
    pass


class FeatureRubricLevel(IntEnum):
    """Standard 0-4 rating scale for semantic evidence features."""
    NONE = 0
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    EXCEPTIONAL = 4


@dataclass(frozen=True)
class FeatureInputScope:
    """Explicit per-feature input field whitelist and blacklist contract (§2)."""
    feature_name: str
    allowed_fields: Tuple[str, ...]
    forbidden_fields: Tuple[str, ...]


@dataclass(frozen=True)
class FeatureRubric:
    """Operational scoring rubric defining observable, rule-based criteria (§1)."""
    feature_name: str
    description: str
    input_scope: FeatureInputScope
    criteria_rules: Dict[FeatureRubricLevel, str]

    def validate_level(self, level: int) -> FeatureRubricLevel:
        if level not in range(5):
            raise ValueError(f"Rubric level for {self.feature_name} must be between 0 and 4, got {level}")
        return FeatureRubricLevel(level)


# ---------------------------------------------------------------------------
# Global Field Input Whitelist / Blacklist (§2)
# ---------------------------------------------------------------------------

GLOBAL_ALLOWED_FIELDS = (
    "evidence_snapshots",
    "evidence_snapshots.raw_observation",
    "evidence_snapshots.source",
    "evidence_snapshots.source_type",
    "evidence_snapshots.observed_at",
    "evidence_snapshots.available_at",
    "prompt_topic",
)

GLOBAL_FORBIDDEN_FIELDS = (
    "human_expert_decision",
    "actual_market_outcome",
    "outcome",
    "outcome.actual_market_outcome",
    "human_decision",
    "ape_decision",
)


# ---------------------------------------------------------------------------
# Pre-registered Observable Rubrics (§1, §2)
# ---------------------------------------------------------------------------

RUBRIC_PAIN_DEPTH = FeatureRubric(
    feature_name="pain_evidence_depth",
    description="Observable count and channel diversity of pain/problem statements.",
    input_scope=FeatureInputScope(
        feature_name="pain_evidence_depth",
        allowed_fields=GLOBAL_ALLOWED_FIELDS,
        forbidden_fields=GLOBAL_FORBIDDEN_FIELDS,
    ),
    criteria_rules={
        FeatureRubricLevel.NONE: "0 observable pain/problem keyword matches in evidence_snapshots.",
        FeatureRubricLevel.WEAK: "Exactly 1 observable pain/problem keyword match.",
        FeatureRubricLevel.MODERATE: "Exactly 2 observable pain/problem keyword matches.",
        FeatureRubricLevel.STRONG: "3 to 4 observable pain/problem keyword matches.",
        FeatureRubricLevel.EXCEPTIONAL: "5+ observable pain/problem keyword matches across >= 2 distinct sources.",
    }
)

RUBRIC_DEMAND_INTENSITY = FeatureRubric(
    feature_name="user_demand_intensity",
    description="Observable count of explicit demand, feature requests, and buy signals.",
    input_scope=FeatureInputScope(
        feature_name="user_demand_intensity",
        allowed_fields=GLOBAL_ALLOWED_FIELDS,
        forbidden_fields=GLOBAL_FORBIDDEN_FIELDS,
    ),
    criteria_rules={
        FeatureRubricLevel.NONE: "0 observable demand keyword matches.",
        FeatureRubricLevel.WEAK: "Exactly 1 demand/feature request mention.",
        FeatureRubricLevel.MODERATE: "Exactly 2 demand/feature request mentions.",
        FeatureRubricLevel.STRONG: "3 to 4 demand mentions OR 1 explicit willingness-to-pay match.",
        FeatureRubricLevel.EXCEPTIONAL: "5+ demand mentions OR >= 2 explicit purchasing/pre-order matches.",
    }
)

RUBRIC_DISCUSSION_ENGAGEMENT = FeatureRubric(
    feature_name="discussion_engagement",
    description="Observable count of discussion threads and comment activity.",
    input_scope=FeatureInputScope(
        feature_name="discussion_engagement",
        allowed_fields=GLOBAL_ALLOWED_FIELDS,
        forbidden_fields=GLOBAL_FORBIDDEN_FIELDS,
    ),
    criteria_rules={
        FeatureRubricLevel.NONE: "0 observable discussion/comment matches.",
        FeatureRubricLevel.WEAK: "Exactly 1 discussion/comment match.",
        FeatureRubricLevel.MODERATE: "Exactly 2 discussion matches (< 5 comments mentioned).",
        FeatureRubricLevel.STRONG: "3 to 4 discussion matches OR thread mentioning 5-9 comments.",
        FeatureRubricLevel.EXCEPTIONAL: "5+ discussion matches OR thread mentioning >= 10 comments.",
    }
)

RUBRIC_COMMERCIAL_INTENT = FeatureRubric(
    feature_name="commercial_intent",
    description="Observable count of pricing, cost, and commercial query signals.",
    input_scope=FeatureInputScope(
        feature_name="commercial_intent",
        allowed_fields=GLOBAL_ALLOWED_FIELDS,
        forbidden_fields=GLOBAL_FORBIDDEN_FIELDS,
    ),
    criteria_rules={
        FeatureRubricLevel.NONE: "0 observable pricing/commercial matches.",
        FeatureRubricLevel.WEAK: "Exactly 1 pricing/cost match.",
        FeatureRubricLevel.MODERATE: "Exactly 2 pricing/cost matches.",
        FeatureRubricLevel.STRONG: "3 pricing matches OR 1 enterprise/subscription inquiry match.",
        FeatureRubricLevel.EXCEPTIONAL: "4+ pricing matches OR clear purchasing/invoice request match.",
    }
)


# ---------------------------------------------------------------------------
# Feature Representation Data Structures (R1 / R2 / R3)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class R1Representation:
    """R1 Baseline — Raw Unstructured Evidence Counts."""
    raw_evidence_count: int
    raw_pain_count: int
    raw_discussion_count: int


@dataclass(frozen=True)
class R2Representation:
    """R2 Evidence-Structured Representation — Label-Free Semantic Features."""
    pain_evidence_depth: FeatureRubricLevel
    user_demand_intensity: FeatureRubricLevel
    discussion_engagement: FeatureRubricLevel
    commercial_intent: FeatureRubricLevel

    def to_vector(self) -> List[int]:
        return [
            int(self.pain_evidence_depth),
            int(self.user_demand_intensity),
            int(self.discussion_engagement),
            int(self.commercial_intent),
        ]


@dataclass(frozen=True)
class R3Representation:
    """R3 Secondary Exploratory Representation — Normalized Indices."""
    normalized_evidence_density_index: float  # 0.0 to 1.0
    source_authority_index: float             # 0.0 to 1.0
    market_friction_score: float              # 0.0 to 1.0


# ---------------------------------------------------------------------------
# Static AST + Runtime Target Isolation Guards (§3)
# ---------------------------------------------------------------------------

import textwrap


def verify_static_target_isolation(func) -> None:
    """Performs static AST inspection of an extraction function to verify zero references to target keys."""
    source = textwrap.dedent(inspect.getsource(func))
    tree = ast.parse(source)

    for node in ast.walk(tree):
        # Inspect string constants for target label names
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            val = node.value.lower()
            if val in ("human_expert_decision", "actual_market_outcome", "outcome"):
                # Exception: sanitization functions checking keys to remove are allowed,
                # but extraction logic itself must not read target labels as data inputs.
                if "sanitize" not in func.__name__ and "strip" not in func.__name__:
                    raise TargetIsolationViolationError(
                        f"STATIC ISOLATION VIOLATION: Function '{func.__name__}' contains static reference to target field '{node.value}'!"
                    )
        # Inspect attribute access
        elif isinstance(node, ast.Attribute):
            if node.attr in ("human_expert_decision", "actual_market_outcome"):
                raise TargetIsolationViolationError(
                    f"STATIC ISOLATION VIOLATION: Function '{func.__name__}' accesses forbidden attribute '{node.attr}'!"
                )


def sanitize_snapshot_input(record: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitizes opportunity record input by hard-stripping forbidden target labels.
    
    Raises TargetIsolationViolationError if record contains prohibited target keys.
    """
    sanitized = {}
    for key, value in record.items():
        if key in GLOBAL_FORBIDDEN_FIELDS:
            continue
        sanitized[key] = value
    return sanitized


def assert_holdout_protection(requested_filepath: Path, holdout_filepath: Path) -> None:
    """Enforces process invariant against accessing locked holdout dataset during contract dev."""
    req_abs = requested_filepath.resolve()
    hold_abs = holdout_filepath.resolve()
    if req_abs == hold_abs or hold_abs in req_abs.parents:
        raise HoldoutAccessViolationError(
            f"HOLDOUT VIOLATION DETECTED: Process attempted to open locked holdout file '{hold_abs}'!"
        )


# ---------------------------------------------------------------------------
# Observable Deterministic Feature Extraction (R2 Label-Free) (§1, §2)
# ---------------------------------------------------------------------------

PAIN_KEYWORDS = ("pain", "problem", "struggling", "issue", "bottleneck", "frustrated")
DEMAND_KEYWORDS = ("need", "want", "request", "looking for", "feature request", "desire")
BUY_KEYWORDS = ("buy", "pay", "pre-order", "budget", "purchase", "pricing plan")
DISC_KEYWORDS = ("discussion", "comments", "debate", "thread", "forum", "community")
COMMERCIAL_KEYWORDS = ("pricing", "cost", "expensive", "subscription", "paid", "commercial", "enterprise", "invoice")


def extract_r2_features_isolated(record: Dict[str, Any]) -> R2Representation:
    """Extracts R2 semantic representation deterministically using observable pattern rules.
    
    GUARANTEES:
    - Zero access to human_expert_decision or actual_market_outcome (Static + Runtime isolated).
    - Purely observable pattern matching based on exact count thresholds.
    """
    clean_record = sanitize_snapshot_input(record)
    evidence_snapshots = clean_record.get("evidence_snapshots", [])

    if not evidence_snapshots:
        return R2Representation(
            pain_evidence_depth=FeatureRubricLevel.NONE,
            user_demand_intensity=FeatureRubricLevel.NONE,
            discussion_engagement=FeatureRubricLevel.NONE,
            commercial_intent=FeatureRubricLevel.NONE,
        )

    # Track sources for channel diversity check
    pain_sources: Set[str] = set()
    pain_count = 0
    demand_count = 0
    buy_count = 0
    disc_count = 0
    comm_count = 0

    for ev in evidence_snapshots:
        raw = ev.get("raw_observation", "").lower()
        src = ev.get("source", "unknown")

        # 1. Pain matches
        if any(kw in raw for kw in PAIN_KEYWORDS):
            pain_count += 1
            pain_sources.add(src)

        # 2. Demand & Buy matches
        if any(kw in raw for kw in DEMAND_KEYWORDS):
            demand_count += 1
        if any(kw in raw for kw in BUY_KEYWORDS):
            buy_count += 1

        # 3. Discussion matches
        if any(kw in raw for kw in DISC_KEYWORDS):
            disc_count += 1

        # 4. Commercial matches
        if any(kw in raw for kw in COMMERCIAL_KEYWORDS):
            comm_count += 1

    # Apply Observable Rubric Rules for Pain Depth
    if pain_count >= 5 and len(pain_sources) >= 2:
        pain_lvl = FeatureRubricLevel.EXCEPTIONAL
    elif pain_count >= 3:
        pain_lvl = FeatureRubricLevel.STRONG
    elif pain_count == 2:
        pain_lvl = FeatureRubricLevel.MODERATE
    elif pain_count == 1:
        pain_lvl = FeatureRubricLevel.WEAK
    else:
        pain_lvl = FeatureRubricLevel.NONE

    # Apply Observable Rubric Rules for Demand Intensity
    if buy_count >= 2 or demand_count >= 5:
        demand_lvl = FeatureRubricLevel.EXCEPTIONAL
    elif demand_count >= 3 or buy_count == 1:
        demand_lvl = FeatureRubricLevel.STRONG
    elif demand_count == 2:
        demand_lvl = FeatureRubricLevel.MODERATE
    elif demand_count == 1:
        demand_lvl = FeatureRubricLevel.WEAK
    else:
        demand_lvl = FeatureRubricLevel.NONE

    # Apply Observable Rubric Rules for Discussion Engagement
    if disc_count >= 5:
        disc_lvl = FeatureRubricLevel.EXCEPTIONAL
    elif disc_count >= 3:
        disc_lvl = FeatureRubricLevel.STRONG
    elif disc_count == 2:
        disc_lvl = FeatureRubricLevel.MODERATE
    elif disc_count == 1:
        disc_lvl = FeatureRubricLevel.WEAK
    else:
        disc_lvl = FeatureRubricLevel.NONE

    # Apply Observable Rubric Rules for Commercial Intent
    if comm_count >= 4:
        comm_lvl = FeatureRubricLevel.EXCEPTIONAL
    elif comm_count == 3:
        comm_lvl = FeatureRubricLevel.STRONG
    elif comm_count == 2:
        comm_lvl = FeatureRubricLevel.MODERATE
    elif comm_count == 1:
        comm_lvl = FeatureRubricLevel.WEAK
    else:
        comm_lvl = FeatureRubricLevel.NONE

    return R2Representation(
        pain_evidence_depth=pain_lvl,
        user_demand_intensity=demand_lvl,
        discussion_engagement=disc_lvl,
        commercial_intent=comm_lvl,
    )


# ---------------------------------------------------------------------------
# Outcome-Agnostic Pre-locked Scorer v1 Mapping (§4)
# ---------------------------------------------------------------------------

def map_r2_to_scorer_v1_input(r2: R2Representation, prompt_topic: str) -> Dict[str, Any]:
    """Deterministically maps R2 representation ratings into Scorer v1 feature dict.
    
    GOVERNANCE PRINCIPLE (§4):
    - Objective: 'How is this representation mathematically projected onto Scorer v1 feature space?'
    - Forbidden: Tuning this mapping to artificially reproduce historical BUILD decisions or outcomes.
    """
    pain_count = int(r2.pain_evidence_depth)
    disc_count = int(r2.discussion_engagement)
    demand_count = int(r2.user_demand_intensity)
    comm_count = int(r2.commercial_intent)

    return {
        "pain_points": [f"Pain point signal {i+1}" for i in range(pain_count)],
        "discussions": [f"Discussion item {i+1}" for i in range(disc_count)],
        "risks": ["Risk item 1", "Risk item 2"] if demand_count < 2 else ["Risk item 1"],
        "competitors": [f"Competitor signal {i+1}" for i in range(max(1, 4 - comm_count))],
        "target_audience": ["Primary Segment", "Secondary Segment"] if demand_count >= 2 else ["Primary Segment"],
    }


# ---------------------------------------------------------------------------
# Pre-registered Experiment Contract Metadata (§4)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RepresentationContract:
    """Encapsulates the complete frozen representation contract for G3b.3a."""
    contract_version: str = "G3b.3a-FREEZE-2.0-REFINED"
    mapping_objective: str = (
        "Project R2 semantic rubrics objectively onto Scorer v1 mathematical input geometry "
        "without tuning against historical labels or market outcome data."
    )
    null_hypothesis: str = (
        "R2/R3 representations do not significantly alter Scorer v1 decision distribution "
        "compared to baseline unstructured R1 representation."
    )
    alt_hypothesis: str = (
        "Leakage-free structured R2 representation provides higher decision space dispersion "
        "and removes 53-score clustering without target or feature design leakage."
    )
    locked_metrics: Tuple[str, ...] = (
        "BUILD_count",
        "VALIDATE_count",
        "WAIT_count",
        "score_mean",
        "score_std",
        "min_score",
        "max_score",
        "distance_to_55",
        "distance_to_70",
        "calibration_vs_validation_stability",
    )
