"""
Evidence Interpretation Layer — P1.5
Contract: P1.4 v2 (sealed 2026-09-01)

Governance boundaries (MUST NOT cross):
  - G3b artifacts: UNCHANGED
  - Scorer v1 (scorer.py): UNCHANGED
  - Calibration / holdout datasets: UNTOUCHED

Design contract:
  - No LLM calls. Extraction is deterministic and reproducible.
  - source_type → classification  ≠  source content → semantic claim
    These are tracked in separate extraction_method values.
  - COMPETITOR requires: (a) named commercial entity + (b) competitive-role evidence.
  - AUDIENCE requires: an economically distinct persona/context.
  - RISK is a feasibility-reducing observable obstacle.
  - FEASIBILITY_POSITIVE is documented but NOT added to risk count.
  - scorer_contribution is NOT computed here — Scorer v1 determines from len().
  - unknown ≠ 0: evidence_present=False is not the same as count=0.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Tuple

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class ClaimType(str, Enum):
    PAIN               = "PAIN"
    DISCUSSION         = "DISCUSSION"
    RISK               = "RISK"
    COMPETITOR         = "COMPETITOR"
    AUDIENCE           = "AUDIENCE"
    DEMAND             = "DEMAND"
    FEASIBILITY_POSITIVE = "FEASIBILITY_POSITIVE"
    MENTION            = "MENTION"


class EvidenceStrength(str, Enum):
    STRONG   = "STRONG"
    MODERATE = "MODERATE"
    WEAK     = "WEAK"


@dataclass
class ConfidenceBasis:
    """Structural provenance for future confidence formula (formula NOT defined here)."""
    supporting_snapshot_ids:  List[str]
    source_count:             int
    independent_source_count: int   # distinct sources contributing to different fields
    contradiction_count:      int
    dimension_coverage:       float  # set by ClaimAggregator after full pass


@dataclass
class EvidenceClaim:
    """
    A single, traceable unit of interpreted evidence.

    Every field is derivable from raw_evidence_snapshots without
    touching G3b, Scorer v1, or any dataset.
    """
    claim_id:           str
    snapshot_ids:       List[str]
    claim_type:         ClaimType
    claim_text:         str
    entity_refs:        List[str]
    evidence_strength:  EvidenceStrength
    scorer_dimension:   str  # "demand" | "feasibility" | "competition" | "revenue"
    scorer_input_field: str  # "pain_points" | "discussions" | "risks" | "competitors" | "target_audience"
    evidence_present:   bool
    is_contradicted:    bool
    confidence_basis:   ConfidenceBasis
    extraction_method:  str  # "keyword_match" | "source_type_map" | "entity_extraction" | "context_extraction"


# ---------------------------------------------------------------------------
# EvidenceInterpreter
# ---------------------------------------------------------------------------

class EvidenceInterpreter:
    """
    Deterministically extracts EvidenceClaim[] from raw evidence snapshots.

    One snapshot can contribute claims to multiple dimensions (see P1.4 v2, §4).
    However, each snapshot contributes at most ONE claim per scorer_input_field
    (dedup rule: PAIN or DEMAND, not both, from the same snapshot).
    """

    # ── Pain signals ──────────────────────────────────────────────────────────
    _PAIN_KWS: Tuple[str, ...] = (
        "pain", "problem", "struggling", "issue", "bottleneck",
        "frustrated", "exhaustion",
    )

    # ── Demand signals (only checked when PAIN not matched for same snapshot) ─
    _DEMAND_KWS: Tuple[str, ...] = (
        "require", "need", "looking for", "feature request",
    )

    # ── Discussion — source_type mapping (structurally authoritative) ─────────
    # NOTE: source_type_map ≠ semantic claim validation.
    # extraction_method is recorded so reviewers can distinguish.
    _DISC_SOURCE_TYPES: FrozenSet[str] = frozenset({
        "community_debate", "forum", "community", "thread", "discussion",
    })
    _DISC_KWS: Tuple[str, ...] = (
        "discussion", "comments", "debate", "thread", "forum", "community",
    )

    # ── Risk obstacles (feasibility-reducing) ─────────────────────────────────
    _RISK_KWS: Tuple[str, ...] = (
        "bottleneck", "exhaustion", "disconnection", "disconnections",
        "outage", "failure", "unstable", "complexity",
    )

    # ── Feasibility-positive (benchmark / technical capability proof) ─────────
    _FEASIBILITY_POSITIVE_KWS: Tuple[str, ...] = (
        "benchmark", "benchmarks", "compression ratio", "compression",
        "latency", "throughput", "sub-10ms",
    )

    # ── Named commercial competitors — require competitive-role evidence too ───
    _COMMERCIAL_ENTITIES: Dict[str, str] = {
        "datadog":      "Datadog",
        "honeycomb":    "Honeycomb",
        "new relic":    "New Relic",
        "dynatrace":    "Dynatrace",
        "splunk":       "Splunk",
        "elastic cloud":"Elastic Cloud",
        "sumo logic":   "Sumo Logic",
    }
    _COMPETITIVE_ROLE_PHRASES: Tuple[str, ...] = (
        "struggling with", "seeking alternative", "seeking lightweight",
        "too expensive", "replacing", "instead of", "vendor lock",
        "alternative to", "observability bills",
    )

    # ── Audience patterns: (observation_patterns, canonical_segment_name) ─────
    # Each pattern must represent an economically distinct segment.
    # Broad terms like "developers" alone are NOT included.
    _AUDIENCE_PATTERNS: Tuple[Tuple[Tuple[str, ...], str], ...] = (
        (
            ("edge kubernetes", "kubernetes cluster", "edge kubernetes cluster"),
            "Edge Kubernetes Teams",
        ),
        (
            ("industrial edge gateway", "industrial edge", "industrial edge gateways"),
            "Industrial Edge Operators",
        ),
    )

    def interpret(self, evidence_snapshots: List[Dict[str, Any]]) -> List[EvidenceClaim]:
        """
        Returns a list of EvidenceClaim extracted from evidence_snapshots.
        Order is deterministic (same input → same output).
        """
        claims: List[EvidenceClaim] = []
        _counter: Dict[str, int] = {}

        def _next_id(snap_id: str, kind: str) -> str:
            key = f"{snap_id}_{kind}"
            _counter[key] = _counter.get(key, 0) + 1
            return f"claim_{snap_id}_{kind}_{_counter[key]:02d}"

        def _basis(snap_id: str, contradiction: int = 0) -> ConfidenceBasis:
            return ConfidenceBasis(
                supporting_snapshot_ids=[snap_id],
                source_count=1,
                independent_source_count=1,
                contradiction_count=contradiction,
                dimension_coverage=0.0,  # updated by ClaimAggregator
            )

        for ev in evidence_snapshots:
            snap_id    = ev.get("snapshot_id", "unknown")
            obs        = ev.get("raw_observation", "")
            obs_lower  = obs.lower()
            source_type = ev.get("source_type", "").lower().strip()
            source     = ev.get("source", "")

            # ── 1. PAIN ───────────────────────────────────────────────────
            pain_hits = [kw for kw in self._PAIN_KWS if kw in obs_lower]
            generated_pain_claim = False
            if pain_hits:
                claims.append(EvidenceClaim(
                    claim_id        = _next_id(snap_id, "pain"),
                    snapshot_ids    = [snap_id],
                    claim_type      = ClaimType.PAIN,
                    claim_text      = (
                        f"Operational pain signal in {snap_id}. "
                        f"Matched keywords: {pain_hits}."
                    ),
                    entity_refs     = [],
                    evidence_strength = EvidenceStrength.MODERATE,
                    scorer_dimension  = "demand",
                    scorer_input_field = "pain_points",
                    evidence_present = True,
                    is_contradicted  = False,
                    confidence_basis = _basis(snap_id),
                    extraction_method = "keyword_match",
                ))
                generated_pain_claim = True

            # ── 2. DEMAND — only if no PAIN claim from this snapshot ──────
            # Avoids double-counting pain_points from a single observation.
            if not generated_pain_claim:
                demand_hits = [kw for kw in self._DEMAND_KWS if kw in obs_lower]
                if demand_hits:
                    claims.append(EvidenceClaim(
                        claim_id        = _next_id(snap_id, "demand"),
                        snapshot_ids    = [snap_id],
                        claim_type      = ClaimType.DEMAND,
                        claim_text      = (
                            f"Functional demand signal in {snap_id}. "
                            f"Matched keywords: {demand_hits}."
                        ),
                        entity_refs     = [],
                        evidence_strength = EvidenceStrength.WEAK,
                        scorer_dimension  = "demand",
                        scorer_input_field = "pain_points",
                        evidence_present = True,
                        is_contradicted  = False,
                        confidence_basis = _basis(snap_id),
                        extraction_method = "keyword_match",
                    ))

            # ── 3. DISCUSSION ─────────────────────────────────────────────
            # source_type_map is structurally authoritative but does NOT
            # guarantee semantic discussion content (P1.4 v2 methodological note).
            from_source_type = source_type in self._DISC_SOURCE_TYPES
            from_kw          = any(kw in obs_lower for kw in self._DISC_KWS)
            if from_source_type or from_kw:
                method = "source_type_map" if from_source_type else "keyword_match"
                strength = EvidenceStrength.MODERATE if from_source_type else EvidenceStrength.WEAK
                claims.append(EvidenceClaim(
                    claim_id        = _next_id(snap_id, "discussion"),
                    snapshot_ids    = [snap_id],
                    claim_type      = ClaimType.DISCUSSION,
                    claim_text      = (
                        f"Community discussion evidence from {snap_id}. "
                        f"Extraction: {method} "
                        f"(source_type={ev.get('source_type','?')!r}, "
                        f"keyword_match={from_kw}). "
                        f"PROVENANCE NOTE: source_type->classification "
                        f"is NOT equivalent to semantic claim validation."
                    ),
                    entity_refs     = [source],
                    evidence_strength = strength,
                    scorer_dimension  = "demand",
                    scorer_input_field = "discussions",
                    evidence_present = True,
                    is_contradicted  = False,
                    confidence_basis = _basis(snap_id),
                    extraction_method = method,
                ))

            # ── 4. FEASIBILITY_POSITIVE vs. RISK ─────────────────────────
            is_benchmark = any(kw in obs_lower for kw in self._FEASIBILITY_POSITIVE_KWS)

            if is_benchmark:
                # Technical feasibility proof — recorded but NOT added to risk count.
                entity_hits = [
                    e for e in ["ClickHouse", "Vector", "ARM64"]
                    if e.lower() in obs_lower
                ]
                claims.append(EvidenceClaim(
                    claim_id        = _next_id(snap_id, "feasibility_positive"),
                    snapshot_ids    = [snap_id],
                    claim_type      = ClaimType.FEASIBILITY_POSITIVE,
                    claim_text      = (
                        f"Technical feasibility proof in {snap_id}: "
                        f"benchmark/performance data present. "
                        f"Recorded as positive counterevidence; NOT counted as risk."
                    ),
                    entity_refs     = entity_hits,
                    evidence_strength = EvidenceStrength.STRONG,
                    scorer_dimension  = "feasibility",
                    scorer_input_field = "risks",  # related field, contribution=0
                    evidence_present = True,
                    is_contradicted  = False,
                    confidence_basis = _basis(snap_id),
                    extraction_method = "keyword_match",
                ))
            else:
                # Risk: feasibility-reducing obstacle
                risk_hits = [kw for kw in self._RISK_KWS if kw in obs_lower]
                if risk_hits:
                    claims.append(EvidenceClaim(
                        claim_id        = _next_id(snap_id, "risk"),
                        snapshot_ids    = [snap_id],
                        claim_type      = ClaimType.RISK,
                        claim_text      = (
                            f"Feasibility obstacle in {snap_id}. "
                            f"Matched keywords: {risk_hits}."
                        ),
                        entity_refs     = [],
                        evidence_strength = EvidenceStrength.MODERATE,
                        scorer_dimension  = "feasibility",
                        scorer_input_field = "risks",
                        evidence_present = True,
                        is_contradicted  = False,
                        confidence_basis = _basis(snap_id),
                        extraction_method = "keyword_match",
                    ))

            # ── 5. COMPETITOR ─────────────────────────────────────────────
            # Both conditions required (P1.4 v2, §2.2):
            #   (a) named commercial entity in observation
            #   (b) competitive-role phrase in same observation
            has_competitive_role = any(
                phrase in obs_lower for phrase in self._COMPETITIVE_ROLE_PHRASES
            )
            if has_competitive_role:
                for entity_key, entity_name in self._COMMERCIAL_ENTITIES.items():
                    if entity_key in obs_lower:
                        claims.append(EvidenceClaim(
                            claim_id        = _next_id(
                                snap_id,
                                f"competitor_{entity_key.replace(' ', '_')}",
                            ),
                            snapshot_ids    = [snap_id],
                            claim_type      = ClaimType.COMPETITOR,
                            claim_text      = (
                                f"Competitor identified: {entity_name}. "
                                f"Competitive-role evidence in {snap_id}: "
                                f"users actively seeking alternatives."
                            ),
                            entity_refs     = [entity_name],
                            evidence_strength = EvidenceStrength.STRONG,
                            scorer_dimension  = "competition",
                            scorer_input_field = "competitors",
                            evidence_present = True,
                            is_contradicted  = False,
                            confidence_basis = _basis(snap_id),
                            extraction_method = "entity_extraction",
                        ))

            # ── 6. AUDIENCE ───────────────────────────────────────────────
            for patterns, segment_name in self._AUDIENCE_PATTERNS:
                if any(p in obs_lower for p in patterns):
                    claims.append(EvidenceClaim(
                        claim_id        = _next_id(
                            snap_id,
                            f"audience_{segment_name.lower().replace(' ', '_')}",
                        ),
                        snapshot_ids    = [snap_id],
                        claim_type      = ClaimType.AUDIENCE,
                        claim_text      = (
                            f"Audience segment identified in {snap_id}: {segment_name}. "
                            f"Economically distinct from other segments."
                        ),
                        entity_refs     = [segment_name],
                        evidence_strength = EvidenceStrength.MODERATE,
                        scorer_dimension  = "revenue",
                        scorer_input_field = "target_audience",
                        evidence_present = True,
                        is_contradicted  = False,
                        confidence_basis = _basis(snap_id),
                        extraction_method = "context_extraction",
                    ))

        return claims
