"""ORION G3b.3c — Forensic Decomposition & Feature Component Analysis Script.

GOVERNANCE INVARIANTS:
- Does NOT touch holdout dataset in any way.
- Does NOT run any schema tests or pytest suites.
- Does NOT alter Scorer v1, RepresentationContract, or calibration dataset.
- Does NOT make normative decisions or tuning changes ("R3 is better", "Scorer v2 required").
- Reads pre-computed evidence from .governance/evidence/g3b3c_ablation_results.jsonl.
- Writes new evidence to .governance/evidence/g3b3c_forensic_decomposition.json.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from ape.intelligence.ablation.representation_contract import (
    extract_r2_features_isolated,
    map_r2_to_scorer_v1_input,
)
from lab.calibration.run_g3b3c_ablation import (
    build_r1_scorer_input,
    build_r3_scorer_input,
)

EVIDENCE_INPUT = REPO_ROOT / ".governance" / "evidence" / "g3b3c_ablation_results.jsonl"
CALIBRATION_PATH = REPO_ROOT / ".governance" / "calibration_dataset_2026.json"
EVIDENCE_OUTPUT = REPO_ROOT / ".governance" / "evidence" / "g3b3c_forensic_decomposition.json"

assert EVIDENCE_INPUT.exists(), f"Input evidence missing: {EVIDENCE_INPUT}"
assert CALIBRATION_PATH.exists(), f"Calibration missing: {CALIBRATION_PATH}"


def load_ablation_results() -> Dict[str, Dict[str, Any]]:
    """Load latest R1, R2, R3 runs from append-only ablation jsonl."""
    runs = {}
    with open(EVIDENCE_INPUT, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            cond = data["condition"]
            runs[cond] = data  # Keep latest run per condition
    return runs


def load_calibration_by_id() -> Dict[str, Dict[str, Any]]:
    with open(CALIBRATION_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)
    return {r["opportunity_id"]: r for r in records}


def analyze_forensic_decomposition():
    ablation_runs = load_ablation_results()
    calib_map = load_calibration_by_id()

    r1_records = {r["opportunity_id"]: r for r in ablation_runs["R1"]["per_record"]}
    r2_records = {r["opportunity_id"]: r for r in ablation_runs["R2"]["per_record"]}
    r3_records = {r["opportunity_id"]: r for r in ablation_runs["R3"]["per_record"]}

    opportunity_ids = list(r1_records.keys())

    decomposition_list = []
    r3_validate_list = []

    for opp_id in opportunity_ids:
        r1 = r1_records[opp_id]
        r2 = r2_records[opp_id]
        r3 = r3_records[opp_id]
        calib_rec = calib_map[opp_id]

        s1 = r1["score"]
        s2 = r2["score"]
        s3 = r3["score"]

        d1 = "VALIDATE" if s1 >= 55 else "WAIT"
        d2 = "VALIDATE" if s2 >= 55 else "WAIT"
        d3 = "VALIDATE" if s3 >= 55 else "WAIT"

        # Feature payloads passed to Scorer v1
        input_r1 = build_r1_scorer_input(calib_rec)
        r2_feat_obj = extract_r2_features_isolated(calib_rec)
        r2_feat = {
            "pain_evidence_depth": int(r2_feat_obj.pain_evidence_depth),
            "user_demand_intensity": int(r2_feat_obj.user_demand_intensity),
            "discussion_engagement": int(r2_feat_obj.discussion_engagement),
            "commercial_intent": int(r2_feat_obj.commercial_intent),
        }
        input_r2 = map_r2_to_scorer_v1_input(r2_feat_obj, calib_rec.get("prompt_topic", ""))
        input_r3 = build_r3_scorer_input(calib_rec)

        item = {
            "opportunity_id": opp_id,
            "prompt_topic": calib_rec.get("prompt_topic", ""),
            "scores": {
                "R1": s1,
                "R2": s2,
                "R3": s3,
            },
            "score_deltas": {
                "R1_to_R2": s2 - s1,
                "R2_to_R3": s3 - s2,
                "R1_to_R3": s3 - s1,
            },
            "decisions": {
                "R1": d1,
                "R2": d2,
                "R3": d3,
            },
            "decision_flips": {
                "R1_vs_R2": d1 != d2,
                "R2_vs_R3": d2 != d3,
                "R1_vs_R3": d1 != d3,
                "transition_pattern": f"{d1} -> {d2} -> {d3}",
            },
            "vectors": {
                "R1": r1["vector"],
                "R2": r2["vector"],
                "R3": r3["vector"],
            },
            "scorer_inputs": {
                "R1": input_r1,
                "R2": input_r2,
                "R3": input_r3,
            },
            "r2_isolated_features": r2_feat,
        }

        decomposition_list.append(item)

        if d3 == "VALIDATE":
            r3_validate_list.append({
                "opportunity_id": opp_id,
                "prompt_topic": calib_rec.get("prompt_topic", ""),
                "R1_score": s1,
                "R2_score": s2,
                "R3_score": s3,
                "R3_vector": r3["vector"],
                "R3_scorer_input": input_r3,
            })

    output_data = {
        "metadata": {
            "analysis_type": "G3b.3c Forensic Decomposition & Component Analysis",
            "holdout_status": "Analytical isolation: PASS; No physical or analytical holdout access during decomposition.",
            "record_count": len(decomposition_list),
            "validate_candidate_count": len(r3_validate_list),
        },
        "r3_validate_candidates": r3_validate_list,
        "records_decomposition": decomposition_list,
    }

    EVIDENCE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(EVIDENCE_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Forensic decomposition evidence written: {EVIDENCE_OUTPUT}")
    return output_data


if __name__ == "__main__":
    analyze_forensic_decomposition()
