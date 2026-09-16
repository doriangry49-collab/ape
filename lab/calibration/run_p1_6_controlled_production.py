"""
P1.6 — Controlled Production Replay
Governance Protocol: P1.6 Constitutional Execution

Integration Pre-flight answer (recorded here):
  run_p1_opportunity_execution.py (P1.1) uses build_r1_scorer_input — OLD LAYER.
  P1.1 is FROZEN as historical evidence. NOT modified.
  This script (P1.6) is the first production path that routes through:
      EvidenceInterpreter -> ClaimAggregator -> Frozen Scorer v1

Changes from P1.1 (explicitly recorded, minimal scope):
  [1] build_r1_scorer_input REPLACED by EvidenceInterpreter + ClaimAggregator
  [2] Artifact filename CHANGED: opportunity_brief_p1_6_edge_analytics.md (new run, no overwrite)
  [3] "Human Expert Review" section label REMOVED (was P1-D07)
  [4] confidence = avg(relevance)*100 REMOVED (was P1-D05); replaced by evidence_coverage struct
  [5] Decision rationale now shows claim_id -> snapshot provenance

Immutable:
  G3b              UNCHANGED
  Scorer v1        FROZEN (scorer.py not modified)
  Calibration      UNTOUCHED
  Holdout          UNTOUCHED
  Thresholds       UNCHANGED (BUILD>=70, VALIDATE>=55, WAIT<55)
  P1.1 artifact    FROZEN (separate file, not overwritten)
  Governance ledger APPEND-ONLY
"""
from __future__ import annotations

import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from ape.intelligence.decision.scorer import Scorer, load_weights
from ape.intelligence.ablation.representation_contract import sanitize_snapshot_input
from ape.intelligence.evidence import EvidenceInterpreter, ClaimAggregator, ClaimType

# Governance Path Anchors
CALIBRATION_PATH = REPO_ROOT / ".governance" / "calibration_dataset_2026.json"
HOLDOUT_PATH     = REPO_ROOT / ".governance" / "holdout_dataset_2026.json"
P1_6_LEDGER      = REPO_ROOT / ".governance" / "evidence" / "p1_6_production_ledger.jsonl"
P1_6_ARTIFACT    = REPO_ROOT / "deliverables" / "opportunity_brief_p1_6_edge_analytics.md"
P1_1_ARTIFACT    = REPO_ROOT / "deliverables" / "opportunity_brief_p1_edge_analytics.md"

# Verify immutability guards
assert CALIBRATION_PATH.exists(), "Calibration missing"
assert HOLDOUT_PATH.exists(), "Holdout missing"
assert not str(CALIBRATION_PATH.resolve()) == str(HOLDOUT_PATH.resolve()), "Path collision"
assert P1_1_ARTIFACT.exists(), "P1.1 artifact must exist and must NOT be overwritten"
assert P1_6_ARTIFACT.resolve() != P1_1_ARTIFACT.resolve(), "P1.6 artifact must be a separate file"


def _strength_icon(s: str) -> str:
    return {"STRONG": "●●●", "MODERATE": "●●○", "WEAK": "●○○"}.get(s, "○○○")


def execute_p1_6_pipeline() -> Dict[str, Any]:
    run_id    = f"p1_6_run_{uuid.uuid4().hex[:8]}"
    run_time  = datetime.now(timezone.utc).isoformat()
    topic     = "Self-Hosted Open-Source Infrastructure & Log Analytics Platform for Edge Deployments"

    # ── Step 0: Integration Pre-Flight ────────────────────────────────────────
    # Explicitly record that P1.1 (old layer) is frozen and this script uses new layer.
    p1_1_hash = hashlib.sha256(P1_1_ARTIFACT.read_bytes()).hexdigest()[:12]
    preflight = {
        "p1_1_artifact_frozen": True,
        "p1_1_artifact_hash_prefix": p1_1_hash,
        "old_layer_used": "build_r1_scorer_input (P1.1 — FROZEN, not used here)",
        "new_layer_used": "EvidenceInterpreter + ClaimAggregator (P1.5, integrated here)",
        "integration_status": "FIRST_PRODUCTION_CONNECTION",
    }

    # ── Step 1: Raw Evidence Collection ───────────────────────────────────────
    raw_evidence_snapshots = [
        {
            "snapshot_id":     "ev_p1_001",
            "source":          "github_discussions",
            "source_type":     "developer_forum",
            "observed_at":     "2026-08-15T14:22:10Z",
            "raw_observation": (
                "High CPU and memory footprint of Grafana Loki and Fluentbit on "
                "low-resource IoT gateway devices created severe bottleneck and "
                "disk space exhaustion issues."
            ),
            "relevance_score": 0.92,
        },
        {
            "snapshot_id":     "ev_p1_002",
            "source":          "hackernews_thread",
            "source_type":     "community_debate",
            "observed_at":     "2026-08-18T09:11:45Z",
            "raw_observation": (
                "Developers struggling with expensive cloud observability bills "
                "(Datadog/Honeycomb) for edge Kubernetes clusters, seeking lightweight "
                "self-hosted alternative."
            ),
            "relevance_score": 0.88,
        },
        {
            "snapshot_id":     "ev_p1_003",
            "source":          "arxiv_preprints",
            "source_type":     "technical_paper",
            "observed_at":     "2026-08-20T11:00:00Z",
            "raw_observation": (
                "Embedded ClickHouse and Vector pipeline benchmarks show 85% compression "
                "ratio and sub-10ms query latency on ARM64 single-board computers."
            ),
            "relevance_score": 0.95,
        },
        {
            "snapshot_id":     "ev_p1_004",
            "source":          "reddit_devops",
            "source_type":     "user_feedback",
            "observed_at":     "2026-08-25T18:40:12Z",
            "raw_observation": (
                "Frequent network disconnections on industrial edge gateways require "
                "robust local buffering and store-and-forward log aggregation features."
            ),
            "relevance_score": 0.85,
        },
    ]

    # Sanitize (strip forbidden target labels)
    sanitized = sanitize_snapshot_input({
        "opportunity_id":     "opp_p1_6_edge_analytics",
        "prompt_topic":       topic,
        "evidence_snapshots": raw_evidence_snapshots,
    })

    # ── Step 2: Evidence Interpretation (NEW LAYER — first production connection) ──
    interpreter = EvidenceInterpreter()
    claims = interpreter.interpret(sanitized["evidence_snapshots"])

    # ── Step 3: Claim Aggregation ──────────────────────────────────────────────
    aggregator = ClaimAggregator()
    aggregated = aggregator.aggregate(claims)
    scorer_input = aggregator.scorer_v1_input(aggregated)
    provenance = aggregated.get("_provenance", {})

    # ── Step 4: Placeholder Assertion (fail-closed) ───────────────────────────
    known_placeholders = {"r1", "r2", "r3", "c1", "seg1", "seg2", "p0", "p1", "p2"}
    all_entries = set(
        scorer_input.get("pain_points", [])
        + scorer_input.get("discussions", [])
        + scorer_input.get("risks", [])
        + scorer_input.get("competitors", [])
        + scorer_input.get("target_audience", [])
    )
    found_placeholders = all_entries & known_placeholders
    if found_placeholders:
        raise RuntimeError(
            f"FAIL-CLOSED: Placeholder tokens in scorer input: {found_placeholders}. "
            f"Evidence Interpretation Layer did not produce evidence-backed entries."
        )

    # ── Step 5: Frozen Scorer v1 Evaluation ───────────────────────────────────
    weights = load_weights(REPO_ROOT)
    scorer  = Scorer(weights)
    score, vector, rationale = scorer.score(scorer_input)

    decision = "WAIT"
    if score >= 70:
        decision = "BUILD"
    elif score >= 55:
        decision = "VALIDATE"

    # ── Step 6: Evidence Coverage (replaces baseless avg(relevance) confidence) ─
    covered_fields = sum([
        len(scorer_input["pain_points"]) > 0,
        len(scorer_input["discussions"]) > 0,
        len(scorer_input["risks"]) > 0,
        len(scorer_input["competitors"]) > 0,
        len(scorer_input["target_audience"]) > 0,
    ])
    coverage = provenance.get("dimension_coverage", covered_fields / 5)
    fp_claims = [c for c in claims if c.claim_type == ClaimType.FEASIBILITY_POSITIVE]

    # Claim type summary for brief
    claim_by_type: Dict[str, List] = {}
    for c in claims:
        claim_by_type.setdefault(c.claim_type.value, []).append(c)

    # Provenance trace lines for brief
    prov_lines = aggregator.provenance_lines(claims, aggregated)

    # ── Step 7: Build Market Opportunity Brief (evidence-driven) ──────────────
    claim_table_rows = "\n".join(
        f"| `{c.claim_id}` | {c.claim_type.value} | {c.snapshot_ids} | "
        f"{_strength_icon(c.evidence_strength.value)} {c.evidence_strength.value} | "
        f"{c.scorer_input_field} | {c.extraction_method} |"
        for c in claims
        if c.evidence_present
    )

    prov_block = "\n".join(f"  {ln}" for ln in prov_lines)

    competitor_section = "\n".join(
        f"- **{ent}** — identified in `{cid}` "
        f"(competitive-role evidence: users actively seeking alternatives)"
        for ent, cid in provenance.get("competitor_entity_to_claim_id", {}).items()
    )

    audience_section = "\n".join(
        f"- **{seg}** — identified in `{cid}`"
        for seg, cid in provenance.get("audience_segment_to_claim_id", {}).items()
    )

    fp_section = "\n".join(
        f"- `{c.claim_id}` ({', '.join(c.entity_refs)}): {c.claim_text[:120]}..."
        for c in fp_claims
    ) or "None recorded."

    rationale_block = "\n".join(f"- {r}" for r in rationale)

    brief = f"""# Market Opportunity Brief: Edge Infrastructure Log Analytics
## P1.6 — Controlled Production Replay

**Run ID:** `{run_id}`
**Generated At:** `{run_time}`
**Topic:** {topic}
**Governance Protocol:** P1.6 Controlled Production (Frozen Scorer v1, Evidence Interpretation Layer v1)

---

## 1. Decision Vector

| Metric | Value | Threshold |
|:---|:---:|:---|
| **Final Score** | **{score} / 100** | BUILD ≥ 70 · VALIDATE 55–69 · WAIT < 55 |
| **Decision** | **`{decision}`** | — |
| **Evidence Coverage** | **{covered_fields}/5 fields** | Proportion of Scorer dimensions with evidence-backed input |

> **Note on Evidence Coverage:** `{covered_fields}/5` means all Scorer v1 input fields have at least one traceable EvidenceClaim. This is NOT equivalent to semantic validity = 100%. It means no placeholder tokens were used. Confidence formula is not yet defined (see P1.4 v2, §7).

### Score Vector Breakdown

| Dimension | Raw Score | Weight | Contribution | Formula |
|:---|:---:|:---:|:---:|:---|
| **Demand** | {vector['demand']} / 100 | 0.30 | {int(vector['demand'] * 0.30)} | pain_points × 15 + discussions × 10 |
| **Feasibility** | {vector['feasibility']} / 100 | 0.30 | {int(vector['feasibility'] * 0.30)} | 100 − risks × 15 |
| **Competition** | {vector['competition']} / 100 | 0.20 | {int(vector['competition'] * 0.20)} | 100 − competitors × 20 |
| **Revenue** | {vector['revenue']} / 100 | 0.20 | {int(vector['revenue'] * 0.20)} | 30 + audiences × 15 |
| **Total** | — | — | **{score}** | — |

---

## 2. Evidence Snapshot Ledger

4 observation, 4 distinct sources, collected 2026-08-15 to 2026-08-25.

| Snapshot | Source | Type | Observed At | Observation (excerpt) |
|:---|:---|:---|:---|:---|
| `ev_p1_001` | github_discussions | developer_forum | 2026-08-15 | Grafana Loki/Fluentbit high CPU & memory on IoT gateways → bottleneck & disk exhaustion |
| `ev_p1_002` | hackernews_thread | community_debate | 2026-08-18 | Developers struggling with Datadog/Honeycomb costs for edge K8s, seeking self-hosted alternative |
| `ev_p1_003` | arxiv_preprints | technical_paper | 2026-08-20 | ClickHouse+Vector: 85% compression, sub-10ms latency on ARM64 single-board computers |
| `ev_p1_004` | reddit_devops | user_feedback | 2026-08-25 | Frequent network disconnections on industrial edge gateways require store-and-forward buffering |

---

## 3. Evidence Interpretation — EvidenceClaim Table

Every Scorer v1 input is derived from the following claims. Zero placeholder tokens.

| Claim ID | Type | Source Snapshots | Strength | Scorer Field | Extraction |
|:---|:---|:---|:---:|:---|:---|
{claim_table_rows}

### Feasibility Counterevidence (FEASIBILITY_POSITIVE — NOT in risks count)

{fp_section}

> **Architectural note:** `FEASIBILITY_POSITIVE` claims are recorded as counterevidence but do NOT reduce the `risks` count in Scorer v1. Scorer v1 formula is `feasibility = 100 − len(risks) × 15`; there is no positive-evidence input channel. This is a known Scorer v1 constraint.

---

## 4. Competitor Analysis

The following competitors were identified from evidence with competitive-role proof:

{competitor_section}

Named competitors (not placeholder `c1`) produce `competition_score = {vector['competition']}` via `100 − {len(scorer_input['competitors'])} × 20`.

---

## 5. Target Audience Segments

The following economically distinct segments were identified from evidence:

{audience_section}

Segments are evidence-backed (not placeholder `seg1/seg2`) via context extraction from raw observations.

---

## 6. Decision Rationale (Scorer v1 Traceability)

Scorer v1 rationale (frozen formula, no tuning):

{rationale_block}

### Provenance Trace (Scorer Input ← Claim ← Snapshot)

```
{prov_block}
```

---

## 7. System Analysis
*(This section is system-generated. It has NOT been reviewed by a human expert.)*

The evidence set shows a coherent demand signal: operational pain (resource exhaustion, disconnection), named commercial alternatives users are actively replacing (Datadog, Honeycomb), and technical feasibility (ARM64 benchmark). The market conclusion — that a lightweight self-hosted edge log analytics platform addresses a real demand — is consistent with the evidence. However, this constitutes **signals requiring validation**, not confirmed market opportunity.

**What this brief does NOT claim:**
- This is not a validated business case.
- Evidence coverage 5/5 does not equal semantic quality = 100%.
- The score of {score} is a Scorer v1 output from 4 observations; it is NOT a market research conclusion.
- FEASIBILITY_POSITIVE evidence (arXiv benchmark) is documented but does not improve the feasibility score in Scorer v1.

---

## 8. Recommended Validation Steps

1. **Customer interview:** 5+ conversations with edge Kubernetes operators and industrial IoT teams to validate willingness-to-pay.
2. **Competitor pricing research:** Verify Datadog/Honeycomb contract sizes at edge scale to quantify the economic gap.
3. **Technical prototype:** Deploy ClickHouse+Vector on ARM64 gateway; reproduce the benchmark under production workload.
4. **Source independence audit:** Verify that ev_p1_001..004 do not originate from the same root report.
5. **Human expert review:** Present this brief to a domain expert before any product or investment decision.

---

## Appendix: Governance

| Item | Value |
|:---|:---|
| Run ID | `{run_id}` |
| Governance Protocol | P1.6 Controlled Production |
| Evidence Interpretation Layer | v1 (P1.5, 2026-09-01) |
| Scorer v1 | FROZEN |
| G3b | UNCHANGED |
| Calibration Dataset | UNTOUCHED |
| Holdout Dataset | UNTOUCHED |
| P1.1 Artifact | FROZEN (`{p1_1_hash}...`) |
| Placeholder Tokens | NONE |
| Dimension Coverage | {covered_fields}/5 |
"""

    # ── Step 8: Write Artifact (new file, P1.1 not overwritten) ───────────────
    P1_6_ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    with open(P1_6_ARTIFACT, "w", encoding="utf-8") as f:
        f.write(brief)

    artifact_hash = hashlib.sha256(P1_6_ARTIFACT.read_bytes()).hexdigest()

    # ── Step 9: Verify P1.1 still untouched ───────────────────────────────────
    p1_1_hash_after = hashlib.sha256(P1_1_ARTIFACT.read_bytes()).hexdigest()[:12]
    assert p1_1_hash_after == p1_1_hash, (
        f"INTEGRITY VIOLATION: P1.1 artifact was modified! "
        f"Before={p1_1_hash} After={p1_1_hash_after}"
    )

    # ── Step 10: Append-only Governance Ledger ────────────────────────────────
    governance_record = {
        "stage":            "P1.6",
        "run_id":           run_id,
        "timestamp":        run_time,
        "topic":            topic,
        "score":            score,
        "decision":         decision,
        "vector":           vector,
        "evidence_coverage": f"{covered_fields}/5",
        "placeholder_tokens": list(found_placeholders),
        "claims_count":     len(claims),
        "scorer_input_counts": {k: len(v) for k, v in scorer_input.items()},
        "competitors_identified": scorer_input["competitors"],
        "audiences_identified":   scorer_input["target_audience"],
        "artifact_path":    str(P1_6_ARTIFACT),
        "artifact_hash":    artifact_hash,
        "p1_1_artifact_hash_prefix_unchanged": (p1_1_hash_after == p1_1_hash),
        "integration_note": "First production use of EvidenceInterpreter+ClaimAggregator",
        "preflight": preflight,
    }

    P1_6_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(P1_6_LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(governance_record, ensure_ascii=False) + "\n")

    return governance_record


if __name__ == "__main__":
    import os

    SEP = "=" * 70
    print(SEP)
    print("  P1.6 -- Controlled Production Replay")
    print("  EvidenceInterpreter + ClaimAggregator + Frozen Scorer v1")
    print(SEP)

    result = execute_p1_6_pipeline()

    print()
    print(f"  Decision:            {result['score']} / {result['decision']}")
    print(f"  Evidence Coverage:   {result['evidence_coverage']} Scorer fields")
    print(f"  Claims Extracted:    {result['claims_count']}")
    print(f"  Placeholder Tokens:  {result['placeholder_tokens'] or 'NONE'}")
    print(f"  Competitors:         {result['competitors_identified']}")
    print(f"  Audiences:           {result['audiences_identified']}")
    print(f"  Scorer Inputs:       {result['scorer_input_counts']}")
    print(f"  P1.1 Artifact:       {'UNCHANGED' if result['p1_1_artifact_hash_prefix_unchanged'] else 'MODIFIED (VIOLATION)'}")
    print()
    print(f"  Artifact:  {result['artifact_path']}")
    print(f"  Hash:      {result['artifact_hash'][:16]}...")
    print(f"  Ledger:    (append-only) {P1_6_LEDGER}")
    print()
    print("  G3b: UNCHANGED | Scorer v1: FROZEN | Calibration/Holdout: UNTOUCHED")
    print(SEP)
