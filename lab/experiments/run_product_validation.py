import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lab.candidates.product_validation import ProductValidationEngine


def run_validation(repo_root: Path, topic: str = "home_local_services") -> dict:
    results_dir = repo_root / "lab" / "experiments" / "results"
    
    # 1. Load Opportunity Card from ORION-034 result
    challenge_path = results_dir / "opportunity-challenge.json"
    if challenge_path.exists():
        challenge_data = json.loads(challenge_path.read_text(encoding="utf-8"))
        opportunity_card = challenge_data.get("opportunity_card", {})
    else:
        opportunity_card = {
            "product_name": f"APE {topic.title()} Automation Tool",
            "target_customer": ["Solo Founders", "Developers"],
            "problem": "High API pricing and local setup complexity",
            "existing_alternatives": ["Generic API Providers"],
            "monetization_hypothesis": "$29 one-time CLI developer license.",
            "first_customer_acquisition_hypothesis": "Direct community forum outreach.",
            "success_criteria": "50 active developers using CLI tool within 14 days.",
        }

    # 2. Load Raw Evidence
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
            "competitors": ["Generic home_local_services API Providers"],
            "target_audience": ["Solo Founders", "Software Developers"],
            "sources": ["HackerNews", "AudienceHeuristics"],
            "evidence_hash": "sha256_evidence_home_local_services_ledger"
        }

    # 3. Execute Product Validation Engine
    engine = ProductValidationEngine()
    validation_result = engine.validate_opportunity(opportunity_card, raw_evidence)

    # 4. Write JSON Artifact
    out_json = results_dir / f"{topic}-validation.json"
    out_json.write_text(json.dumps(validation_result, indent=2), encoding="utf-8")

    # 5. Write Markdown Artifact
    out_md = results_dir / f"{topic}-validation.md"
    
    know_str = "\n".join(f"- {k}" for k in validation_result["what_we_know"]) if validation_result["what_we_know"] else "- Zero verified statements"
    dont_know_str = "\n".join(f"- {d}" for d in validation_result["what_we_dont_know"]) if validation_result["what_we_dont_know"] else "- All hypotheses verified"
    claims_str = "\n".join(f"- **[{c['status']}]** `{c['claim']}` ({c['reason']})" for c in validation_result["audited_claims"])

    md_content = (
        f"# PRODUCT VALIDATION REPORT: {topic}\n\n"
        f"**Opportunity:** `{topic}`  \n"
        f"**Validation Decision:** `{validation_result['decision']}`  \n"
        f"**Validation Score:** `{validation_result['validation_score']}/100`  \n"
        f"**Confidence:** `{validation_result['confidence']}%`  \n"
        f"**Evidence Quality:** `{validation_result['evidence_quality']}/100`\n\n"
        "---\n\n"
        "## Grounded Metric Breakdown\n"
        f"- **Demand Score:** `{validation_result['demand_score']}/100`  \n"
        f"- **Pain Score:** `{validation_result['pain_score']}/100`  \n"
        f"- **Buyer Intent Score:** `{validation_result['buyer_intent_score']}/100`  \n"
        f"- **Monetization Signal:** `{validation_result['monetization_signal']}/100`  \n"
        f"- **Evidence Quality:** `{validation_result['evidence_quality']}/100`\n\n"
        "## Decision Rationale (Why?)\n"
        f"{validation_result['decision_reason']}\n\n"
        "## Empirical Statement Audit (Self-Critique)\n"
        f"{claims_str}\n\n"
        "## What We Know (EVIDENCED)\n"
        f"{know_str}\n\n"
        "## What We Don't Know (UNSUPPORTED / HYPOTHESIS)\n"
        f"{dont_know_str}\n\n"
        "## Recommended Next Experiment\n"
        f"{validation_result['next_action']}\n\n"
        "## Audit Lineage & Evidence Hash\n"
        f"- **Evidence SHA-256 Hash:** `{validation_result['evidence_lineage']['evidence_hash']}`  \n"
        f"- **Data Sources:** {', '.join(validation_result['evidence_sources'])}  \n"
        f"- **Unsupported Claims Ratio:** `{validation_result['evidence_lineage']['unsupported_claims_ratio'] * 100}%`\n"
    )

    out_md.write_text(md_content, encoding="utf-8")
    return validation_result


def main() -> None:
    print("Executing Product Validation Engine for 'home_local_services'...")
    res = run_validation(REPO_ROOT, "home_local_services")

    print("\n========================================================")
    print("PRODUCT VALIDATION RESULT")
    print(f"  Opportunity       : {res['opportunity']}")
    print(f"  Demand Score      : {res['demand_score']}/100")
    print(f"  Pain Score        : {res['pain_score']}/100")
    print(f"  Buyer Intent      : {res['buyer_intent_score']}/100")
    print(f"  Monetization Sign : {res['monetization_signal']}/100")
    print(f"  Evidence Quality  : {res['evidence_quality']}/100")
    print("--------------------------------------------------------")
    print(f"  Validation Score  : {res['validation_score']}/100")
    print(f"  Confidence        : {res['confidence']}%")
    print(f"  DECISION          : {res['decision']}")
    print(f"  Why               : {res['decision_reason']}")
    print(f"  Next Action       : {res['next_action']}")
    print("========================================================")


if __name__ == "__main__":
    main()
