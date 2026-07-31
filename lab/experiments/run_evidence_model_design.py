import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lab.candidates.real_user_evidence_ingestion import RealUserEvidenceIngestionValidator
from lab.candidates.evidence_taxonomy import EvidenceTaxonomyModel


def run_evidence_model_design(repo_root: Path, topic: str = "home_local_services") -> dict:
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

    # Ingestion validation
    validator = RealUserEvidenceIngestionValidator()
    clean_responses, ingestion_errors = validator.validate_responses(raw_responses)

    # Evaluate Taxonomy Model
    model = EvidenceTaxonomyModel()
    report = model.evaluate_model(topic, clean_responses)
    report["ingestion_errors"] = ingestion_errors

    # Mandatory Engineering Assessment
    engineering_assessment = {
        "orion_role": "Development Engineer (Three Mandatory Layers: Implementation, Verification, Engineering Judgment).",
        "task_validity_critique": (
            "ORION-044 correctly shifts focus from inventing fake numeric thresholds to formalizing an epistemic evidence taxonomy. "
            "It enforces that stated survey optimism cannot be conflated with observed transaction behavior."
        ),
        "confidence_score_critique": (
            "Single numeric confidence scores (e.g. 35% confidence with 0 real users) create false precision. "
            "APE MUST use multi-dimensional coverage metrics (completeness, quality, diversity, coverage, uncertainty)."
        ),
        "implementation_recommendation": "OPTION B: Lab-level Evidence Model Refactor (Keep src/ape/ untouched; formalize taxonomy in lab/).",
        "next_orion_step": "Maintain firm technical stop (user_responses.json = []). Await human operator evidence collection.",
        "engineering_recommendation": "REFACTOR",
    }
    report["engineering_assessment"] = engineering_assessment

    # Save JSON Artifact
    out_json = results_dir / "evidence-model-design.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Save Markdown Artifact
    cat_rows = "\n".join(
        f"| `{k}` | {v['definition']} | `{v['epistemic_weight']}` | `{v['can_trigger_GO']}` | `{v['can_trigger_NOGO']}` |"
        for k, v in report["categories"].items()
    )

    md_content = (
        f"# ORION-044 Engineering Report: Evidence Model Design & Taxonomy ({topic})\n\n"
        f"**ENGINEERING RECOMMENDATION:** `{engineering_assessment['engineering_recommendation']}`\n"
        f"**Experiment:** `ORION-044`\n"
        f"**Status:** `{report['status']}`\n"
        f"**Observed Real User Count:** `{report['observed_real_user_count']}`\n\n"
        "---\n\n"
        "## 1. Executive Summary\n"
        "ORION-044 formalizes the 11-category Epistemic Evidence Taxonomy for APE, strictly separating STATED_INTENT (survey optimism) from OBSERVED_BEHAVIOR (verified execution/payment). Single numeric confidence percentages are replaced by multi-dimensional epistemic coverage metrics.\n\n"
        "## 2. Engineering Judgment & Critique Protocol\n"
        "Orion operates across three mandatory responsibilities: (1) Implementation, (2) Verification, (3) Engineering Judgment. Orion actively critiques task assumptions, rejects arbitrary heuristics, and ensures technical alignment with APE's core goals.\n\n"
        "## 3. Current Evidence Model Critique\n"
        "Uniform hypothesis scoring (treating H1 Problem, H2 Payment, and H3 Trial as equal survey counts) is flawed. Payment and trial intents require behavioral proof (OBSERVED_PAYMENT, OBSERVED_USAGE), whereas survey responses are merely STATED_INTENT (weight 0.3x).\n\n"
        "## 4. Proposed 11-Category Evidence Taxonomy\n\n"
        "| Category | Definition | Epistemic Weight | Can Trigger GO? | Can Trigger NO-GO? |\n"
        "| :--- | :--- | :---: | :---: | :---: |\n"
        f"{cat_rows}\n\n"
        "## 5. Evidence Diversity & Sampling Analysis\n"
        "To mitigate Channel & Selection Bias, APE requires corroboration across $\\ge 2$ independent sources (e.g. HN + Reddit + Direct Interview) before evaluating high-confidence evidence.\n\n"
        "## 6. Decision Contract & Epistemic Conditions\n"
        "- `0 Responses` $\\rightarrow$ `VALIDATE_MORE` (EMPTY != NEGATIVE).\n"
        "- `Dominant Negative Evidence` $\\rightarrow$ `NO-GO`.\n"
        "- `STATED_INTENT Alone` $\\rightarrow$ CANNOT trigger `GO` without `OBSERVED_BEHAVIOR`.\n"
        "- `OBSERVED_BEHAVIOR + Corroboration` $\\rightarrow$ Prerequisite for `GO` candidate.\n\n"
        "## 7. Confidence Model Critique\n"
        f"{report['confidence_score_critique']}\n\n"
        "## 8. Implementation Recommendation\n"
        f"**Recommendation:** `{engineering_assessment['implementation_recommendation']}`\n\n"
        "## 9. Risks & Objections\n"
        "- Risk of survey respondents over-promising hypothetical payment.\n"
        "- Risk of single-channel sampling bias.\n\n"
        "## 10. Self-Critique & Invariants\n"
        "- INFERRED != OBSERVED enforced.\n"
        "- SYNTHETIC != REAL enforced.\n"
        "- EMPTY != NEGATIVE enforced.\n"
        "- PROVISIONAL_THRESHOLD != OBSERVED MARKET FACT enforced.\n\n"
        "## 11. MANDATORY ENGINEERING ASSESSMENT (Orion Judgment)\n\n"
        f"1. **Orion Protocol Role:** {engineering_assessment['orion_role']}\n"
        f"2. **Task Validity Critique:** {engineering_assessment['task_validity_critique']}\n"
        f"3. **Confidence Metric Critique:** {engineering_assessment['confidence_score_critique']}\n"
        f"4. **Implementation Decision:** {engineering_assessment['implementation_recommendation']}\n"
        f"5. **Next Logical Step:** {engineering_assessment['next_orion_step']}\n"
        f"6. **Final Recommendation:** **`{engineering_assessment['engineering_recommendation']}`**\n"
    )

    out_md = results_dir / "evidence-model-design.md"
    out_md.write_text(md_content, encoding="utf-8")
    return report


def main() -> None:
    print("Executing ORION-044 Evidence Model Design & Engineering Report for 'home_local_services'...")
    res = run_evidence_model_design(REPO_ROOT, "home_local_services")

    print("\n========================================================")
    print("ORION-044 EVIDENCE MODEL DESIGN RESULT")
    print(f"  Experiment                 : {res['experiment']}")
    print(f"  Status                     : {res['status']}")
    print(f"  Observed Real User Count   : {res['observed_real_user_count']}")
    print(f"  Engineering Recommendation : {res['engineering_assessment']['engineering_recommendation']}")
    print("--------------------------------------------------------")
    print(f"  Implementation Choice      : {res['engineering_assessment']['implementation_recommendation']}")
    print(f"  Epistemic Uncertainty      : {res['epistemic_metrics']['epistemic_uncertainty']}")
    print("========================================================")


if __name__ == "__main__":
    main()
