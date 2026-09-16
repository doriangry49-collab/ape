"""ORION G3b.3c — R1/R2/R3 Ablation Runner.

Runs three representation conditions (R1, R2, R3) against the 30-record
calibration dataset using frozen RepresentationContract_v1.0 and Scorer v1.

GOVERNANCE INVARIANTS (per Şef 2026-09-01 GO):
- Contract, Scorer v1, calibration dataset, holdout: UNTOUCHED.
- Rubric, feature extraction, threshold: NOT modified based on results.
- Each R1/R2/R3 run recorded separately, append-only.
- Results observed ONLY. No G3b.4/Scorer v2 decisions from this script.
"""

import json
import sys
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

# ── Path anchor ──────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ape.intelligence.decision.scorer import Scorer, load_weights
from ape.intelligence.ablation.representation_contract import (
    extract_r2_features_isolated,
    map_r2_to_scorer_v1_input,
    sanitize_snapshot_input,
    RepresentationContract,
)

# ── Governance: holdout guard ─────────────────────────────────────────────────
CALIBRATION_PATH = REPO_ROOT / ".governance" / "calibration_dataset_2026.json"
HOLDOUT_PATH = REPO_ROOT / ".governance" / "holdout_dataset_2026.json"

assert CALIBRATION_PATH.exists(), f"Calibration dataset missing: {CALIBRATION_PATH}"
assert not str(CALIBRATION_PATH.resolve()) == str(HOLDOUT_PATH.resolve()), \
    "HOLDOUT GUARD: calibration and holdout paths must differ."

CONTRACT = RepresentationContract()


# ── R1: Raw Unstructured Baseline ────────────────────────────────────────────

def build_r1_scorer_input(record: Dict[str, Any]) -> Dict[str, Any]:
    """R1 Baseline — unstructured raw evidence counts mapped naively to Scorer v1."""
    clean = sanitize_snapshot_input(record)
    evidence = clean.get("evidence_snapshots", [])
    topic = clean.get("prompt_topic", "").lower()

    pain_count = sum(
        1 for ev in evidence
        if any(kw in ev.get("raw_observation", "").lower()
               for kw in ("pain", "problem", "struggling", "issue", "bottleneck", "frustrated"))
    )
    disc_count = sum(
        1 for ev in evidence
        if any(kw in ev.get("raw_observation", "").lower()
               for kw in ("discussion", "comments", "debate", "thread", "forum", "community"))
    )
    is_hardware = any(kw in topic for kw in ("hardware", "robot", "sensor", "device", "iot"))

    return {
        "pain_points": [f"p{i}" for i in range(pain_count)],
        "discussions": [f"d{i}" for i in range(disc_count)],
        "risks": ["r1", "r2", "r3"] if is_hardware else ["r1", "r2"],
        "competitors": ["c1"],
        "target_audience": ["seg1", "seg2"],
    }


# ── R3: Normalized Index Representation ──────────────────────────────────────

def build_r3_scorer_input(record: Dict[str, Any]) -> Dict[str, Any]:
    """R3 — normalized evidence density and source authority indices."""
    clean = sanitize_snapshot_input(record)
    evidence = clean.get("evidence_snapshots", [])
    topic = clean.get("prompt_topic", "").lower()

    total = len(evidence)
    density = min(total / 5.0, 1.0)  # normalized 0-1 over 5 max reference

    authority_sources = {"github", "hackernews", "producthunt", "ycombinator", "arxiv"}
    high_auth_count = sum(
        1 for ev in evidence
        if any(auth in ev.get("source", "").lower() for auth in authority_sources)
    )
    authority_ratio = high_auth_count / total if total > 0 else 0.0

    # Map indices to Scorer v1 feature counts
    pain_proxy = max(0, round(density * 3))
    disc_proxy = max(0, round(authority_ratio * 3))
    is_hardware = any(kw in topic for kw in ("hardware", "robot", "sensor", "device", "iot"))

    return {
        "pain_points": [f"p{i}" for i in range(pain_proxy)],
        "discussions": [f"d{i}" for i in range(disc_proxy)],
        "risks": ["r1", "r2", "r3"] if is_hardware else ["r1", "r2"],
        "competitors": ["c1"],
        "target_audience": ["seg1", "seg2"],
    }


# ── Ablation Core ─────────────────────────────────────────────────────────────

def run_ablation_condition(
    records: List[Dict[str, Any]],
    condition: str,
    scorer: Scorer,
) -> Dict[str, Any]:
    """Run one ablation condition (R1 / R2 / R3) over all calibration records."""
    results = []

    for record in records:
        opp_id = record["opportunity_id"]
        topic = record.get("prompt_topic", "")

        # Build scorer input per condition — NO target labels used
        if condition == "R1":
            scorer_input = build_r1_scorer_input(record)
        elif condition == "R2":
            r2 = extract_r2_features_isolated(record)
            scorer_input = map_r2_to_scorer_v1_input(r2, topic)
        elif condition == "R3":
            scorer_input = build_r3_scorer_input(record)
        else:
            raise ValueError(f"Unknown condition: {condition}")

        score, vector, rationale = scorer.score(scorer_input)

        results.append({
            "opportunity_id": opp_id,
            "prompt_topic": topic,
            "condition": condition,
            "score": score,
            "vector": vector,
            "rationale": rationale,
        })

    scores = [r["score"] for r in results]
    build_count = sum(1 for s in scores if s >= 70)
    validate_count = sum(1 for s in scores if 55 <= s < 70)
    wait_count = sum(1 for s in scores if s < 55)
    score_mean = sum(scores) / len(scores)
    score_std = math.sqrt(sum((s - score_mean) ** 2 for s in scores) / len(scores))
    distance_55 = [abs(s - 55) for s in scores]
    distance_70 = [abs(s - 70) for s in scores]

    return {
        "condition": condition,
        "contract_version": CONTRACT.contract_version,
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "record_count": len(records),
        "summary": {
            "BUILD_count": build_count,
            "VALIDATE_count": validate_count,
            "WAIT_count": wait_count,
            "score_mean": round(score_mean, 3),
            "score_std": round(score_std, 3),
            "min_score": min(scores),
            "max_score": max(scores),
            "mean_distance_to_55": round(sum(distance_55) / len(distance_55), 3),
            "mean_distance_to_70": round(sum(distance_70) / len(distance_70), 3),
        },
        "per_record": results,
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("ORION G3b.3c — R1/R2/R3 Ablation")
    print(f"Contract: {CONTRACT.contract_version}")
    print(f"Dataset : {CALIBRATION_PATH}")
    print(f"Started : {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)
    print()

    # Load calibration dataset (NOT holdout)
    with open(CALIBRATION_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)
    print(f"Loaded {len(records)} calibration records.")

    # Load Scorer v1 (FROZEN — not modified)
    weights = load_weights(REPO_ROOT)
    scorer = Scorer(weights)
    print(f"Scorer v1 loaded. Weights: {weights}")
    print()

    all_results = {}

    for condition in ["R1", "R2", "R3"]:
        print(f"--- Running condition: {condition} ---")
        result = run_ablation_condition(records, condition, scorer)
        all_results[condition] = result

        s = result["summary"]
        print(f"  BUILD={s['BUILD_count']}  VALIDATE={s['VALIDATE_count']}  WAIT={s['WAIT_count']}")
        print(f"  score_mean={s['score_mean']}  score_std={s['score_std']}")
        print(f"  min={s['min_score']}  max={s['max_score']}")
        print(f"  mean_dist_55={s['mean_distance_to_55']}  mean_dist_70={s['mean_distance_to_70']}")
        print()

    # Print comparative summary
    print("=" * 70)
    print("ABLATION COMPARATIVE SUMMARY")
    print("=" * 70)
    print(f"{'Metric':<30} {'R1':>10} {'R2':>10} {'R3':>10}")
    print("-" * 62)
    metrics = [
        ("BUILD_count", "BUILD_count"),
        ("VALIDATE_count", "VALIDATE_count"),
        ("WAIT_count", "WAIT_count"),
        ("score_mean", "score_mean"),
        ("score_std", "score_std"),
        ("min_score", "min_score"),
        ("max_score", "max_score"),
        ("mean_distance_to_55", "mean_distance_to_55"),
        ("mean_distance_to_70", "mean_distance_to_70"),
    ]
    for label, key in metrics:
        r1_val = all_results["R1"]["summary"][key]
        r2_val = all_results["R2"]["summary"][key]
        r3_val = all_results["R3"]["summary"][key]
        print(f"  {label:<28} {str(r1_val):>10} {str(r2_val):>10} {str(r3_val):>10}")

    print()
    print(f"Null hypothesis  : {CONTRACT.null_hypothesis}")
    print(f"Alt hypothesis   : {CONTRACT.alt_hypothesis}")
    print()

    # Write append-only evidence file
    output_path = REPO_ROOT / ".governance" / "evidence" / "g3b3c_ablation_results.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "a", encoding="utf-8") as f:
        for condition, result in all_results.items():
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

    print(f"Evidence written (append-only): {output_path}")
    print()
    print("GOVERNANCE REMINDER:")
    print("  - Scorer v1, contract, calibration dataset, holdout: UNTOUCHED.")
    print("  - Results observed only. No rubric/protocol changes from this run.")
    print("  - G3b.4 / Scorer v2 decisions require separate GO.")
    print()
    print("G3b.3c ablation complete.")

    return all_results


if __name__ == "__main__":
    main()
