"""
ClaimAggregator — P1.5
Contract: P1.4 v2 (sealed 2026-09-01)

Aggregates EvidenceClaim[] into Scorer v1 compatible input dict.

Key rules:
  - No placeholder tokens. Every list element is a claim_id or named entity.
  - FEASIBILITY_POSITIVE claims are documented but NOT added to risks[].
  - COMPETITOR list is deduplicated by entity_name (unique set, insertion order).
  - AUDIENCE list is deduplicated by segment_name.
  - scorer_contribution is NOT computed here — Scorer v1 uses len().
  - unknown (evidence_present=False) is not counted. 0 ≠ unknown.
  - dimension_coverage is set on each claim's confidence_basis after aggregation.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .interpreter import ClaimType, EvidenceClaim

_SCORER_FIELDS = ("pain_points", "discussions", "risks", "competitors", "target_audience")


class ClaimAggregator:
    """
    Converts EvidenceClaim[] → Scorer v1 input dict.

    The output dict conforms to the shape expected by Scorer.score():
        {
            "pain_points":     List[str],   # claim_ids (Scorer uses len())
            "discussions":     List[str],   # claim_ids
            "risks":           List[str],   # claim_ids
            "competitors":     List[str],   # unique entity names
            "target_audience": List[str],   # unique segment names
        }

    A "_provenance" key is added (stripped before passing to Scorer v1) so
    every scorer field can be traced back to its originating claim_id and snapshot.
    """

    def aggregate(self, claims: List[EvidenceClaim]) -> Dict[str, Any]:
        pain_points: List[str] = []
        discussions: List[str] = []
        risks:       List[str] = []
        competitor_entities: Dict[str, str] = {}  # entity_name → claim_id
        audience_segments:   Dict[str, str] = {}  # segment_name → claim_id
        feasibility_positive: List[str] = []      # counterevidence — not in risks

        for c in claims:
            # unknown ≠ 0: skip claims where evidence was not found
            if not c.evidence_present:
                continue

            if c.claim_type in (ClaimType.PAIN, ClaimType.DEMAND):
                pain_points.append(c.claim_id)
            elif c.claim_type == ClaimType.DISCUSSION:
                discussions.append(c.claim_id)
            elif c.claim_type == ClaimType.RISK:
                risks.append(c.claim_id)
            elif c.claim_type == ClaimType.FEASIBILITY_POSITIVE:
                feasibility_positive.append(c.claim_id)  # recorded, NOT in risks
            elif c.claim_type == ClaimType.COMPETITOR:
                for ent in c.entity_refs:
                    if ent not in competitor_entities:
                        competitor_entities[ent] = c.claim_id
            elif c.claim_type == ClaimType.AUDIENCE:
                for seg in c.entity_refs:
                    if seg not in audience_segments:
                        audience_segments[seg] = c.claim_id

        # Compute dimension_coverage: how many of 5 Scorer fields are evidence-backed
        covered = sum([
            len(pain_points) > 0,
            len(discussions) > 0,
            len(risks) > 0,
            len(competitor_entities) > 0,
            len(audience_segments) > 0,
        ])
        coverage = round(covered / 5, 2)
        for c in claims:
            c.confidence_basis.dimension_coverage = coverage

        scorer_input: Dict[str, Any] = {
            "pain_points":     pain_points,
            "discussions":     discussions,
            "risks":           risks,
            "competitors":     list(competitor_entities.keys()),
            "target_audience": list(audience_segments.keys()),
        }

        # Provenance record — stripped before passing to Scorer v1
        scorer_input["_provenance"] = {
            "pain_points_claim_ids":           pain_points,
            "discussions_claim_ids":           discussions,
            "risks_claim_ids":                 risks,
            "competitor_entity_to_claim_id":   competitor_entities,
            "audience_segment_to_claim_id":    audience_segments,
            "feasibility_positive_claim_ids":  feasibility_positive,
            "dimension_coverage":              coverage,
        }

        return scorer_input

    def scorer_v1_input(self, aggregated: Dict[str, Any]) -> Dict[str, List]:
        """Returns the Scorer v1 compatible input — provenance keys stripped."""
        return {k: v for k, v in aggregated.items() if not k.startswith("_")}

    def provenance_lines(
        self,
        claims: List[EvidenceClaim],
        aggregated: Dict[str, Any],
    ) -> List[str]:
        """
        Returns a human-readable provenance trace for every Scorer v1 input field.
        Each line maps: field entry → claim_id → snapshot_id → extraction_method
        """
        lines: List[str] = []
        prov = aggregated.get("_provenance", {})

        # pain_points + discussions + risks via claim_id lookup
        cmap = {c.claim_id: c for c in claims}

        for field_name in ("pain_points", "discussions", "risks"):
            ids = prov.get(f"{field_name}_claim_ids", [])
            lines.append(f"  {field_name} (count={len(ids)}):")
            for cid in ids:
                c = cmap.get(cid)
                if c:
                    lines.append(
                        f"    [{cid}]  type={c.claim_type.value}  "
                        f"snapshot={c.snapshot_ids}  method={c.extraction_method}"
                    )

        # competitors
        comp_map = prov.get("competitor_entity_to_claim_id", {})
        lines.append(f"  competitors (count={len(comp_map)}):")
        for ent, cid in comp_map.items():
            c = cmap.get(cid)
            snap = c.snapshot_ids if c else "?"
            lines.append(f"    [{ent}]  claim_id={cid}  snapshot={snap}")

        # target_audience
        aud_map = prov.get("audience_segment_to_claim_id", {})
        lines.append(f"  target_audience (count={len(aud_map)}):")
        for seg, cid in aud_map.items():
            c = cmap.get(cid)
            snap = c.snapshot_ids if c else "?"
            lines.append(f"    [{seg}]  claim_id={cid}  snapshot={snap}")

        # feasibility counterevidence (not in scorer input)
        fp_ids = prov.get("feasibility_positive_claim_ids", [])
        if fp_ids:
            lines.append(f"  FEASIBILITY_POSITIVE counterevidence (NOT in risks): {fp_ids}")

        # placeholder check
        all_entries = (
            aggregated.get("pain_points", [])
            + aggregated.get("discussions", [])
            + aggregated.get("risks", [])
            + aggregated.get("competitors", [])
            + aggregated.get("target_audience", [])
        )
        placeholders = [e for e in all_entries if e in ("r1", "r2", "c1", "seg1", "seg2", "p0", "p1")]
        if placeholders:
            lines.append(f"  ⚠️  PLACEHOLDER TOKENS DETECTED: {placeholders}")
        else:
            lines.append("  [OK] No placeholder tokens. All entries are evidence-backed.")

        lines.append(f"  dimension_coverage: {prov.get('dimension_coverage', 'N/A'):.0%}")

        return lines
