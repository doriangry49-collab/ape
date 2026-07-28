from pathlib import Path
from typing import Dict, List, Tuple

import yaml


def load_weights(project_root: Path) -> dict:
    weights_path = project_root / ".governance" / "decision_weights.yaml"
    if not weights_path.exists():
        return {"demand": 0.30, "feasibility": 0.30, "competition": 0.20, "revenue": 0.20}
    with open(weights_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

class Scorer:
    def __init__(self, weights: dict):
        self.weights = weights

    def score(self, research_data: dict) -> Tuple[int, Dict[str, int], List[str]]:
        """
        Calculates scores based on the research data.
        Returns overall_score, vector_scores (0-100), and rationale list.
        """
        # Calculate raw scores (0 to 100 range)
        pain_points = len(research_data.get("pain_points", []))
        discussions = len(research_data.get("discussions", []))
        risks = len(research_data.get("risks", []))
        competitors = len(research_data.get("competitors", []))
        audience = len(research_data.get("target_audience", []))
        
        # Demand: more pain points and discussions = higher demand
        raw_demand = min(100, (pain_points * 15) + (discussions * 10))
        
        # Feasibility: more risks = lower feasibility
        raw_feasibility = max(0, 100 - (risks * 15))
        
        # Competition: more competitors = lower score (harder)
        raw_competition = max(0, 100 - (competitors * 20))
        
        # Revenue: basic heuristic on audience size
        raw_revenue = min(100, 30 + (audience * 15))

        vector_scores = {
            "demand": raw_demand,
            "feasibility": raw_feasibility,
            "competition": raw_competition,
            "revenue": raw_revenue
        }

        # Apply weights
        w_demand = self.weights.get("demand", 0.30)
        w_feasibility = self.weights.get("feasibility", 0.30)
        w_comp = self.weights.get("competition", 0.20)
        w_rev = self.weights.get("revenue", 0.20)

        c_demand = int(raw_demand * w_demand)
        c_feasibility = int(raw_feasibility * w_feasibility)
        c_comp = int(raw_competition * w_comp)
        c_rev = int(raw_revenue * w_rev)

        overall_score = c_demand + c_feasibility + c_comp + c_rev

        rationale = [
            f"Demand +{c_demand} "
            f"(from {pain_points} pain points, {discussions} discussions, weight {w_demand})",
            f"Feasibility +{c_feasibility} (from {risks} risks, weight {w_feasibility})",
            f"Competition +{c_comp} (from {competitors} competitors, weight {w_comp})",
            f"Revenue +{c_rev} (from {audience} audiences, weight {w_rev})",
            f"Total = {overall_score}"
        ]

        return overall_score, vector_scores, rationale
