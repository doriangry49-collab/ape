import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lab.candidates.real_user_evidence import RealUserEvidenceEvaluator


def run_real_user_evidence(repo_root: Path, topic: str = "home_local_services") -> dict:
    results_dir = repo_root / "lab" / "experiments" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    input_file = repo_root / "lab" / "experiments" / "input" / "user_responses.json"
    if input_file.exists():
        try:
            user_responses = json.loads(input_file.read_text(encoding="utf-8"))
        except Exception:
            user_responses = []
    else:
        user_responses = []

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

    evaluator = RealUserEvidenceEvaluator()
    report = evaluator.evaluate_real_user_evidence(topic, raw_evidence, user_responses)

    # Save JSON report
    out_json = results_dir / f"{topic}-real-user-evidence.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Save 19-Section Markdown report
    pos_str = "\n".join(f"- {p}" for p in report["positive_evidence"]) if report["positive_evidence"] else "- None observed yet (0 responses)"
    neg_str = "\n".join(f"- {n}" for n in report["negative_evidence"]) if report["negative_evidence"] else "- None observed yet"
    know_str = "\n".join(f"- {k}" for k in report["what_we_know"])
    dont_know_str = "\n".join(f"- {d}" for d in report["what_we_dont_know"])

    md_content = (
        f"# Real User Evidence Evaluation Report: {topic}\n\n"
        f"## 1. Validation Objective\n"
        f"{report['validation_objective']}\n\n"
        f"## 2. Hypotheses\n"
        f"- **H1 (Problem):** {report['hypotheses']['H1_problem']}\n"
        f"- **H2 (Payment Intent):** {report['hypotheses']['H2_payment_intent']}\n"
        f"- **H3 (Acquisition):** {report['hypotheses']['H3_acquisition']}\n\n"
        f"## 3. Real Responses Observed\n"
        f"**Count:** `{report['real_responses_observed_count']}/{report['target_response_goal']}`  \n"
        f"**Status:** `{report['status']}`  \n"
        f"**Input Source:** `{report['evidence_lineage']['input_file']}`\n\n"
        f"## 4. Positive Evidence\n"
        f"{pos_str}\n\n"
        f"## 5. Negative Evidence\n"
        f"{neg_str}\n\n"
        f"## 6. Problem Confirmation\n"
        f"**Confirmed Count:** `{report['problem_confirmation_count']}/{report['real_responses_observed_count']}`\n\n"
        f"## 7. Payment Intent\n"
        f"**Commercial Intent Count:** `{report['payment_intent_count']}/{report['real_responses_observed_count']}`\n\n"
        f"## 8. Trial Intent\n"
        f"**Alpha Opt-In Count:** `{report['trial_intent_count']}/{report['real_responses_observed_count']}`\n\n"
        f"## 9. Target Customer Fit\n"
        f"**Qualified Buyer Match:** `{report['target_customer_fit_count']}/{report['real_responses_observed_count']}`\n\n"
        f"## 10. Acquisition Signal\n"
        f"{report['acquisition_signal']}\n\n"
        f"## 11. Observed vs Inferred\n"
        f"{report['observed_vs_inferred']}\n\n"
        f"## 12. Evidence Quality\n"
        f"**Score:** `{report['evidence_quality']}/100`\n\n"
        f"## 13. Confidence\n"
        f"**Confidence Level:** `{report['confidence']}%`\n\n"
        f"## 14. Decision\n"
        f"**DECISION:** `{report['decision']}`\n\n"
        f"## 15. Why (Decision Reason)\n"
        f"{report['decision_reason']}\n\n"
        f"## 16. What We Know\n"
        f"{know_str}\n\n"
        f"## 17. What We Don't Know\n"
        f"{dont_know_str}\n\n"
        f"## 18. Next Action\n"
        f"{report['next_action']}\n\n"
        f"## 19. Evidence Lineage\n"
        f"- **SHA-256 Evidence Hash:** `{report['evidence_lineage']['evidence_hash']}`  \n"
        f"- **Data Sources:** {', '.join(report['evidence_lineage']['sources'])}  \n"
        f"- **Has Synthetic Data:** `{report['evidence_lineage']['has_synthetic']}`\n"
    )

    out_md = results_dir / f"{topic}-real-user-evidence.md"
    out_md.write_text(md_content, encoding="utf-8")
    return report


def main() -> None:
    print("Executing Real User Evidence Evaluation for 'home_local_services'...")
    res = run_real_user_evidence(REPO_ROOT, "home_local_services")

    print("\n========================================================")
    print("REAL USER EVIDENCE RESULT")
    print(f"  Opportunity             : {res['opportunity']}")
    print(f"  Observed Responses      : {res['real_responses_observed_count']}/10")
    print(f"  Status                  : {res['status']}")
    print(f"  DECISION                : {res['decision']}")
    print(f"  Confidence              : {res['confidence']}%")
    print(f"  Reason                  : {res['decision_reason']}")
    print(f"  Next Action             : {res['next_action']}")
    print("========================================================")


if __name__ == "__main__":
    main()
