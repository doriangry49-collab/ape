import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ape.intelligence.decision.scorer import Scorer
from ape.intelligence.research.engine import ResearchEngine
from ape.project import Project
from lab.candidates.opportunity_intelligence import ExperimentalOpportunityScorer


def run_experiment(project_root: Path, topics: list[str]) -> dict[str, dict]:
    """
    Runs production heuristic vs R&D experimental scorer across target topics.
    Saves results to lab/experiments/results/.
    """
    project = Project.load(project_root)
    research_engine = ResearchEngine(project, offline=True)
    prod_scorer = Scorer(weights={"demand": 0.30, "feasibility": 0.30, "competition": 0.20, "revenue": 0.20})
    exp_scorer = ExperimentalOpportunityScorer()

    results_dir = project_root / "lab" / "experiments" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    experiment_summary = {}

    for topic in topics:
        # Fetch research data
        research_report = research_engine.run_research(topic)
        slug = topic.lower().replace(" ", "_")
        
        # Load JSON representation
        research_json_path = project_root / ".build" / "research" / f"{slug}.json"
        if research_json_path.exists():
            research_data = json.loads(research_json_path.read_text(encoding="utf-8"))
        else:
            research_data = {
                "topic": topic,
                "pain_points": research_report.pain_points,
                "discussions": research_report.discussions,
                "competitors": research_report.competitors,
                "target_audience": research_report.target_audience,
                "market_signals": research_report.market_signals,
                "risks": research_report.risks,
                "confidence": research_report.confidence,
                "sources": research_report.sources,
            }

        # 1. Production Heuristic Score
        prod_score, prod_vectors, prod_rationale = prod_scorer.score(research_data)

        # 2. Experimental R&D Opportunity Score
        exp_results = exp_scorer.evaluate_opportunity(research_data)

        topic_result = {
            "topic": topic,
            "production_heuristic": {
                "score": prod_score,
                "vectors": prod_vectors,
                "rationale": prod_rationale,
            },
            "experimental_rd": {
                "score": exp_results["experimental_score"],
                "recommendation": exp_results["recommendation"],
                "recommendation_reason": exp_results["recommendation_reason"],
                "dimensions": exp_results["dimensions"],
                "reasoning": exp_results["reasoning"],
            },
        }

        experiment_summary[topic] = topic_result

        # Save JSON comparison artifact
        json_file = results_dir / f"{slug}_comparison.json"
        json_file.write_text(json.dumps(topic_result, indent=2), encoding="utf-8")

        # Save Markdown comparison artifact
        md_file = results_dir / f"{slug}_comparison.md"
        md_content = (
            f"# R&D Opportunity Intelligence Comparison: {topic}\n\n"
            "## Summary\n"
            f"- **Production Heuristic Score:** `{prod_score}/100`\n"
            f"- **Experimental R&D Score:** `{exp_results['experimental_score']}/100`\n"
            f"- **Experimental Recommendation:** `{exp_results['recommendation']}`\n"
            f"- **Reasoning:** {exp_results['recommendation_reason']}\n\n"
            "## Production Heuristic Vectors\n"
            + "\n".join(f"- **{k}:** {v}" for k, v in prod_vectors.items()) + "\n\n"
            "## R&D 6-Dimensional Breakdown\n"
            + "\n".join(f"- **{k}:** {v}" for k, v in exp_results["dimensions"].items()) + "\n\n"
            "## Detailed R&D Reasoning\n"
            + "\n".join(f"- {r}" for r in exp_results["reasoning"])
        )
        md_file.write_text(md_content, encoding="utf-8")

    return experiment_summary


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent.parent
    topics = ["ai_agents", "home_local_services"]
    print(f"Running Market Opportunity Intelligence R&D Experiment on topics: {topics}")
    
    summary = run_experiment(repo_root, topics)
    for topic, res in summary.items():
        print(f"\n========================================================")
        print(f"Topic: {topic}")
        print(f"  Production Heuristic Score : {res['production_heuristic']['score']}/100")
        print(f"  Experimental R&D Score     : {res['experimental_rd']['score']}/100")
        print(f"  Experimental Recommendation: {res['experimental_rd']['recommendation']}")
        print(f"  Recommendation Reason      : {res['experimental_rd']['recommendation_reason']}")
        print(f"========================================================")


if __name__ == "__main__":
    main()
