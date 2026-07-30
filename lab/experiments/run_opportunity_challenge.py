import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lab.candidates.opportunity_challenge import OpportunityChallengeEvaluator


def run_challenge(results_dir: Path) -> dict:
    """
    Loads opportunity briefs, evaluates candidates, selects winner, and writes challenge artifacts.
    """
    topics = ["ai_agents", "home_local_services", "real_estate"]
    briefs = []

    for topic in topics:
        json_path = results_dir / f"{topic}-opportunity-brief.json"
        if json_path.exists():
            briefs.append(json.loads(json_path.read_text(encoding="utf-8")))

    evaluator = OpportunityChallengeEvaluator()
    challenge_result = evaluator.evaluate_candidates(briefs)

    # Save JSON result
    out_json = results_dir / "opportunity-challenge.json"
    out_json.write_text(json.dumps(challenge_result, indent=2), encoding="utf-8")

    # Save Markdown result
    out_md = results_dir / "opportunity-challenge.md"

    decision = challenge_result["decision"]
    rankings_str = "\n".join(
        f"- **{r['topic']}**: Total Score = `{r['total_score']}/100` (Action: `{r['action']}`)"
        for r in challenge_result.get("rankings", [])
    )

    if decision == "GO":
        card = challenge_result["opportunity_card"]
        md_content = (
            "# APE Opportunity Challenge: Winner Selection & Product Opportunity Card\n\n"
            f"**Final Decision:** `GO`  \n"
            f"**Winning Opportunity:** `{challenge_result['winner_topic']}` (Total Challenge Score: `{challenge_result['winner_score']}/100`)\n\n"
            "---\n\n"
            "## Candidate Opportunity Rankings\n"
            f"{rankings_str}\n\n"
            "---\n\n"
            "# WINNING PRODUCT OPPORTUNITY CARD\n\n"
            f"**Product Name:** `{card['product_name']}`  \n"
            f"**Target Customer:** {', '.join(card['target_customer'])}  \n"
            f"**Smallest Useful MVP:** {card['smallest_useful_mvp']}\n\n"
            "## 1. Problem Statement\n"
            f"{card['problem']}\n\n"
            "## 2. Existing Alternatives & Specific Gap\n"
            f"**Alternatives:** {', '.join(card['existing_alternatives'])}\n\n"
            f"**Identified Niche Gap:** {card['specific_gap']}\n\n"
            "## 3. Proposed Solution & Core Features\n"
            f"{card['proposed_solution']}\n\n"
            "### 3–5 Core MVP Features:\n"
            + "\n".join(f"- {f}" for f in card['core_features']) + "\n\n"
            "## 4. What NOT to Build (Scope Boundaries)\n"
            + "\n".join(f"- {n}" for n in card['what_not_to_build']) + "\n\n"
            "## 5. Commercial & Go-To-Market Hypotheses\n"
            f"- **Monetization Hypothesis:** {card['monetization_hypothesis']}  \n"
            f"- **Acquisition Hypothesis:** {card['first_customer_acquisition_hypothesis']}  \n"
            f"- **Validation Experiment:** {card['validation_experiment']}\n\n"
            "## 6. Success Criteria & Evidence Lineage\n"
            f"- **Success Criteria:** {card['success_criteria']}  \n"
            f"- **Evidence SHA-256 Hash:** `{card['evidence_lineage']['evidence_hash']}`  \n"
            f"- **Data Sources:** {', '.join(card['evidence_lineage']['sources'])}\n"
        )
    else:
        md_content = (
            "# APE Opportunity Challenge: Winner Selection\n\n"
            f"**Final Decision:** `NO-GO`  \n"
            f"**Reason:** {challenge_result['no_go_reason']}\n\n"
            "## Candidate Opportunity Rankings\n"
            f"{rankings_str}\n"
        )

    out_md.write_text(md_content, encoding="utf-8")
    return challenge_result


def main() -> None:
    results_dir = REPO_ROOT / "lab" / "experiments" / "results"
    print("Running APE Opportunity Challenge Evaluation...")
    result = run_challenge(results_dir)

    print("\n========================================================")
    print(f"Decision: {result['decision']}")
    if result["decision"] == "GO":
        print(f"Winning Topic : {result['winner_topic']}")
        print(f"Winner Score  : {result['winner_score']}/100")
        print(f"Product Name  : {result['opportunity_card']['product_name']}")
    else:
        print(f"NO-GO Reason  : {result['no_go_reason']}")
    print("========================================================")


if __name__ == "__main__":
    main()
