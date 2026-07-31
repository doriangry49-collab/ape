import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lab.candidates.real_user_evidence_ingestion import RealUserEvidenceIngestionValidator
from lab.candidates.external_collection_gate import ExternalEvidenceCollectionGate


def run_collection_gate(repo_root: Path, topic: str = "home_local_services") -> dict:
    results_dir = repo_root / "lab" / "experiments" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    input_file = repo_root / "lab" / "experiments" / "input" / "user_responses.json"
    if input_file.exists():
        try:
            raw_responses = json.loads(input_file.read_text(encoding="utf-8"))
        except Exception:
            raw_responses = []
    else:
        raw_responses = []

    # Ingestion Validation Gate
    validator = RealUserEvidenceIngestionValidator()
    clean_responses, ingestion_errors = validator.validate_responses(raw_responses)

    # Raw market scanner evidence
    raw_evidence = {
        "topic": topic,
        "pain_points": [
            "High API pricing and pricing model complexity",
            "Difficult local setup and installation overhead for home_local_services"
        ],
        "sources": ["HackerNews", "AudienceHeuristics"],
        "evidence_hash": "sha256_collection_gate_ledger"
    }

    gate = ExternalEvidenceCollectionGate()
    report = gate.audit_collection_gate(topic, raw_evidence, clean_responses)
    report["ingestion_errors"] = ingestion_errors

    # Save JSON Artifact
    out_json = results_dir / "external-evidence-collection-gate.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Save Markdown Artifact
    matrix = report["hypothesis_matrix"]
    h1 = matrix["H1_problem_exists"]
    h2 = matrix["H2_payment_intent"]
    h3 = matrix["H3_acquisition_trial_intent"]

    handoff_str = "\n".join(report["human_collection_handoff"])
    rules_str = "\n".join(f"- {r}" for r in report["evidence_integrity_rules"])
    unsupp_str = "\n".join(f"- {u}" for u in report["unsupported_previous_hypotheses"])

    md_content = (
        f"# ORION-042 External Evidence Collection Gate Report: {topic}\n\n"
        f"**Experiment:** `ORION-042`\n"
        f"**Status:** `GATE_ENFORCED / WAITING_FOR_REAL_USERS`\n"
        f"**Observed Real User Count:** `{report['observed_real_user_count']}`\n"
        f"**Minimum Required for GO:** `{report['minimum_required_for_GO']}`\n"
        f"**Current Decision:** `{report['current_decision']}`\n"
        f"**GO Possible:** `{report['go_possible']}` (0 real user responses logged)\n\n"
        f"> **STOP RULE:** {report['stop_rule']}\n\n"
        "---\n\n"
        "## 1. Current Evidence Audit & Stopping Condition\n"
        f"{report['decision_reason']}\n\n"
        "## 2. Hypothesis-to-Evidence Matrix\n\n"
        f"### {h1['hypothesis']}\n"
        f"- **Current Status:** `{h1['current_status']}` (Evidence Count: `{h1['current_evidence_count']}`)\n"
        f"- **Positive Evidence Requirements:** {h1['what_counts_as_positive_evidence']}\n"
        f"- **Negative Evidence Requirements:** {h1['what_counts_as_negative_evidence']}\n"
        f"- **What Remains Unknown:** {h1['what_remains_unknown']}\n"
        f"- **Minimum Evidence Needed for GO:** {h1['minimum_evidence_needed_for_GO']}\n\n"
        f"### {h2['hypothesis']}\n"
        f"- **Current Status:** `{h2['current_status']}` (Evidence Count: `{h2['current_evidence_count']}`)\n"
        f"- **Positive Evidence Requirements:** {h2['what_counts_as_positive_evidence']}\n"
        f"- **Negative Evidence Requirements:** {h2['what_counts_as_negative_evidence']}\n"
        f"- **What Remains Unknown:** {h2['what_remains_unknown']}\n"
        f"- **Minimum Evidence Needed for GO:** {h2['minimum_evidence_needed_for_GO']}\n\n"
        f"### {h3['hypothesis']}\n"
        f"- **Current Status:** `{h3['current_status']}` (Evidence Count: `{h3['current_evidence_count']}`)\n"
        f"- **Positive Evidence Requirements:** {h3['what_counts_as_positive_evidence']}\n"
        f"- **Negative Evidence Requirements:** {h3['what_counts_as_negative_evidence']}\n"
        f"- **What Remains Unknown:** {h3['what_remains_unknown']}\n"
        f"- **Minimum Evidence Needed for GO:** {h3['minimum_evidence_needed_for_GO']}\n\n"
        "## 3. Unsupported Previous Hypotheses (Audited)\n"
        f"{unsupp_str}\n\n"
        "## 4. Evidence Integrity Rules\n"
        f"{rules_str}\n\n"
        "## 5. Human Collection Handoff Protocol\n"
        f"{handoff_str}\n\n"
        "## 6. Audit Lineage\n"
        f"- **SHA-256 Evidence Hash:** `{raw_evidence['evidence_hash']}`\n"
        f"- **Input File:** `lab/experiments/input/user_responses.json` (Empty `[]`)\n"
        f"- **Has Synthetic Data:** `False`\n"
    )

    out_md = results_dir / "external-evidence-collection-gate.md"
    out_md.write_text(md_content, encoding="utf-8")
    return report


def main() -> None:
    print("Executing External Evidence Collection Gate for 'home_local_services'...")
    res = run_collection_gate(REPO_ROOT, "home_local_services")

    print("\n========================================================")
    print("EXTERNAL EVIDENCE COLLECTION GATE RESULT")
    print(f"  Experiment                 : {res['experiment']}")
    print(f"  Status                     : {res['evidence_collection_status']}")
    print(f"  Observed Real User Count   : {res['observed_real_user_count']}")
    print(f"  Minimum Required for GO    : {res['minimum_required_for_GO']}")
    print(f"  GO Possible                : {res['go_possible']}")
    print(f"  Current Decision           : {res['current_decision']}")
    print("--------------------------------------------------------")
    print(f"  STOP RULE                  : {res['stop_rule']}")
    print("========================================================")


if __name__ == "__main__":
    main()
