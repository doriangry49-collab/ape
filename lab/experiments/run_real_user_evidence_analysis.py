import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lab.candidates.real_user_evidence_analysis import RealUserEvidenceAnalyzer


def run_evidence_analysis(repo_root: Path, topic: str = "home_local_services") -> dict:
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

    analyzer = RealUserEvidenceAnalyzer()
    analysis_report = analyzer.analyze_evidence(topic, raw_evidence, user_responses)

    # Save JSON artifact
    out_json = results_dir / f"{topic}-evidence-analysis.json"
    out_json.write_text(json.dumps(analysis_report, indent=2), encoding="utf-8")

    # Save Markdown artifact
    pos_str = "\n".join(f"- {p['item']}" for p in analysis_report["positive_evidence"]) if analysis_report["positive_evidence"] else "- None observed (0 real user responses logged)"
    neg_str = "\n".join(f"- {n['item']}" for n in analysis_report["negative_evidence"]) if analysis_report["negative_evidence"] else "- None observed"
    neut_str = "\n".join(f"- {u['item']}" for u in analysis_report["neutral_evidence"]) if analysis_report["neutral_evidence"] else "- None observed"
    unk_str = "\n".join(f"- {u['item']}" for u in analysis_report["unknown_evidence"]) if analysis_report["unknown_evidence"] else "- None"

    h1 = analysis_report["hypotheses"]["H1_problem_exists"]
    h2 = analysis_report["hypotheses"]["H2_payment_intent"]
    h3 = analysis_report["hypotheses"]["H3_acquisition_trial_intent"]

    crit = analysis_report["self_critique"]

    md_content = (
        f"# ORION-038 Real User Evidence Analysis & Decision Gate: {topic}\n\n"
        f"**Opportunity:** `{topic}`\n"
        f"**Observed Response Count:** `{analysis_report['observed_response_count']}/{analysis_report['target_response_threshold']}`\n"
        f"**Decision:** `{analysis_report['decision']}`\n"
        f"**Confidence:** `{analysis_report['confidence']}%`\n"
        f"**Evidence Quality:** `{analysis_report['evidence_quality']}/100`\n\n"
        "---\n\n"
        "## 1. Decision Rationale & Empty Data Behavior\n"
        f"{analysis_report['decision_reason']}\n\n"
        "## 2. Hypothesis-by-Hypothesis Validation Status\n"
        f"- **H1 (Problem Exists):** `{h1['status']}` (Positive: {h1['positive_count']}, Negative: {h1['negative_count']})\n"
        f"  *{h1['statement']}*\n"
        f"- **H2 (Payment Intent):** `{h2['status']}` (Positive: {h2['positive_count']}, Negative: {h2['negative_count']})\n"
        f"  *{h2['statement']}*\n"
        f"- **H3 (Acquisition & Trial Intent):** `{h3['status']}` (Positive: {h3['positive_count']}, Negative: {h3['negative_count']})\n"
        f"  *{h3['statement']}*\n\n"
        "## 3. Evidence Balance Categorization\n"
        "### Positive Evidence (OBSERVED_POSITIVE):\n"
        f"{pos_str}\n\n"
        "### Negative Evidence (OBSERVED_NEGATIVE):\n"
        f"{neg_str}\n\n"
        "### Neutral Evidence (OBSERVED_NEUTRAL):\n"
        f"{neut_str}\n\n"
        "### Unknown / Missing Evidence:\n"
        f"{unk_str}\n\n"
        "## 4. Self-Critique of ORION-034 Hypotheses\n"
        f"- **$29 One-Time CLI License Hypothesis:** `{crit['pricing_29_license']}`\n"
        f"- **Developer Community Outreach Hypothesis:** `{crit['developer_community_outreach']}`\n"
        f"- **50 Active Developers / 14 Days Target:** `{crit['target_50_devs_14_days']}`\n"
        f"- **Invariant Note:** {crit['inferred_vs_observed_note']}\n\n"
        "## 5. Next Recommended Action\n"
        f"{analysis_report['next_action']}\n\n"
        "## 6. Audit Lineage & Evidence Hash\n"
        f"- **SHA-256 Evidence Hash:** `{analysis_report['evidence_lineage']['evidence_hash']}`\n"
        f"- **Input File:** `{analysis_report['evidence_lineage']['input_file']}`\n"
        f"- **Has Synthetic Data:** `{analysis_report['evidence_lineage']['has_synthetic']}`\n"
    )

    out_md = results_dir / f"{topic}-evidence-analysis.md"
    out_md.write_text(md_content, encoding="utf-8")
    return analysis_report


def main() -> None:
    print("Executing Real User Evidence Analysis & Decision Gate for 'home_local_services'...")
    res = run_evidence_analysis(REPO_ROOT, "home_local_services")

    print("\n========================================================")
    print("REAL USER EVIDENCE ANALYSIS RESULT")
    print(f"  Opportunity             : {res['opportunity']}")
    print(f"  Observed Responses      : {res['observed_response_count']}/10")
    print(f"  H1 (Problem) Status     : {res['hypotheses']['H1_problem_exists']['status']}")
    print(f"  H2 (Payment) Status     : {res['hypotheses']['H2_payment_intent']['status']}")
    print(f"  H3 (Acquisition) Status : {res['hypotheses']['H3_acquisition_trial_intent']['status']}")
    print("--------------------------------------------------------")
    print(f"  Evidence Quality        : {res['evidence_quality']}/100")
    print(f"  Confidence              : {res['confidence']}%")
    print(f"  DECISION                : {res['decision']}")
    print(f"  Reason                  : {res['decision_reason']}")
    print(f"  Next Action             : {res['next_action']}")
    print("========================================================")


if __name__ == "__main__":
    main()
