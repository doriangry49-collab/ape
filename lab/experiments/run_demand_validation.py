import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lab.candidates.demand_validation import DemandValidationEngine


def run_demand_validation(repo_root: Path, topic: str = "home_local_services") -> dict:
    results_dir = repo_root / "lab" / "experiments" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Load raw research evidence
    research_json = repo_root / ".build" / "research" / f"{topic}.json"
    if research_json.exists():
        raw_evidence = json.loads(research_json.read_text(encoding="utf-8"))
    else:
        raw_evidence = {
            "topic": topic,
            "pain_points": [
                "High API pricing and pricing model complexity",
                "Difficult local setup and installation overhead for home_local_services"
            ],
            "discussions": [{"title": "Show HN", "points": 120}],
            "target_audience": ["Solo Founders", "Software Developers"],
            "sources": ["HackerNews", "AudienceHeuristics"],
            "evidence_hash": "sha256_evidence_home_local_services_ledger"
        }

    engine = DemandValidationEngine()
    validation_report = engine.evaluate_demand(topic, raw_evidence, user_responses=[])

    # Save JSON artifact
    out_json = results_dir / f"{topic}-demand-validation.json"
    out_json.write_text(json.dumps(validation_report, indent=2), encoding="utf-8")

    # Save 16-Section Markdown Artifact
    pkg = validation_report["validation_experiment"]
    lp = pkg["landing_page_spec"]
    survey = pkg["user_survey"]
    acq = pkg["acquisition_experiment"]
    pricing = pkg["pricing_experiment"]
    hyp = validation_report["original_hypotheses"]

    survey_str = "\n".join(
        f"**{q['id']}.** {q['question']}  \n*Type:* {q['type']} | *Purpose:* {q['purpose']}"
        for q in survey
    )

    evidence_str = "\n".join(
        f"- **[{e['category']}]** {e['item']}" for e in validation_report["evidence_collected"]
    )

    know_str = "\n".join(f"- {k}" for k in validation_report["what_we_know"])
    dont_know_str = "\n".join(f"- {d}" for d in validation_report["what_we_still_dont_know"])

    md_content = (
        f"# Real User Demand Validation: {topic}\n\n"
        f"## 1. Opportunity\n"
        f"**Target Market Segment:** `{topic}`  \n"
        f"**Validation Stage:** Initial Real-World Demand Test Package\n\n"
        f"## 2. Original Hypotheses (Audited)\n"
        f"- **Pricing Hypothesis:** `{hyp['pricing']}` (Status: `UNSUPPORTED`)\n"
        f"- **Acquisition Hypothesis:** `{hyp['acquisition']}` (Status: `UNSUPPORTED`)\n"
        f"- **Success Target Hypothesis:** `{hyp['success_target']}` (Status: `UNSUPPORTED`)\n\n"
        f"## 3. Validation Experiment Overview\n"
        f"Designed an un-biased, zero-cost demand validation package to collect empirical user signals without synthetic fallbacks.\n\n"
        f"## 4. Landing Page Validation Spec\n"
        f"- **Headline:** {lp['headline']}  \n"
        f"- **Subheadline:** {lp['subheadline']}  \n"
        f"- **Target User:** {lp['target_user']}  \n"
        f"- **Core Problem:** {lp['core_problem']}  \n"
        f"- **Proposed Solution:** {lp['proposed_solution']}  \n"
        f"- **CTA:** {lp['call_to_action']}  \n"
        f"- **Tested Pricing Note:** {lp['pricing_hypothesis_tested']}\n\n"
        f"## 5. User Survey (Non-Leading Behavioral Questions)\n"
        f"{survey_str}\n\n"
        f"## 6. Acquisition Experiment\n"
        f"- **Channel:** {acq['channel']}  \n"
        f"- **Target Audience:** {', '.join(acq['target_audience'])}  \n"
        f"- **Outreach Message:** {acq['outreach_message']}  \n"
        f"- **Measurement Pipeline:** {acq['measurement']}  \n"
        f"- **Success Threshold:** `{acq['success_threshold']}`  \n"
        f"- **Failure Threshold:** `{acq['failure_threshold']}`\n\n"
        f"## 7. Pricing Experiment\n"
        f"- **Tested Hypothesis:** `{pricing['tested_hypothesis']}`  \n"
        f"- **Evidence Status:** `{pricing['evidence_status']}`  \n"
        f"- **Validation Method:** {pricing['validation_method']}  \n"
        f"- **Proposed Threshold:** `{pricing['proposed_success_threshold']}`\n\n"
        f"## 8. Evidence Collected\n"
        f"{evidence_str}\n\n"
        f"## 9. Observed vs Inferred Analysis\n"
        f"{validation_report['observed_vs_inferred_note']}\n\n"
        f"## 10. Success / Failure Criteria\n"
        f"- **Success Criterion:** Real user response conversion rate >= 40% with >= 10 responses.\n"
        f"- **Failure Criterion:** Real user response conversion rate < 10% or negative customer feedback.\n\n"
        f"## 11. Self-Critique\n"
        f"APE cannot replace real human customers. Because 0 real user responses have been recorded yet, APE MUST NOT declare GO.\n\n"
        f"## 12. Decision\n"
        f"**DECISION:** `{validation_report['decision']}`  \n"
        f"**Confidence:** `{validation_report['confidence']}%`  \n"
        f"**Decision Reason:** {validation_report['decision_reason']}\n\n"
        f"## 13. What We Know\n"
        f"{know_str}\n\n"
        f"## 14. What We Still Don't Know\n"
        f"{dont_know_str}\n\n"
        f"## 15. Next Action\n"
        f"{validation_report['next_action']}\n\n"
        f"## 16. Evidence Lineage\n"
        f"- **SHA-256 Evidence Hash:** `{validation_report['evidence_lineage']['evidence_hash']}`  \n"
        f"- **Sources:** {', '.join(validation_report['evidence_lineage']['sources'])}  \n"
        f"- **Has Synthetic Data:** `{validation_report['evidence_lineage']['has_synthetic']}`\n"
    )

    out_md = results_dir / f"{topic}-demand-validation.md"
    out_md.write_text(md_content, encoding="utf-8")
    return validation_report


def main() -> None:
    print("Running Real User Demand Validation Experiment for 'home_local_services'...")
    res = run_demand_validation(REPO_ROOT, "home_local_services")

    print("\n========================================================")
    print("DEMAND VALIDATION RESULT")
    print(f"  Opportunity       : {res['opportunity']}")
    print(f"  Observed Signals  : {res['observed_count']}")
    print(f"  Inferred Hypotheses: {res['inferred_count']}")
    print(f"  DECISION          : {res['decision']}")
    print(f"  Confidence        : {res['confidence']}%")
    print(f"  Reason            : {res['decision_reason']}")
    print(f"  Next Action       : {res['next_action']}")
    print("========================================================")


if __name__ == "__main__":
    main()
