from typing import Dict, Tuple


class ConstitutionValidator:
    """
    Ensures that the raw scores comply with the APE constitution
    and maps them to a concrete decision and policy.
    """
    def validate(self, overall_score: int, vector_scores: Dict[str, int]) -> Tuple[str, str, str]:
        """
        Returns (decision, policy, next_step)
        """
        feasibility = vector_scores.get("feasibility", 0)
        demand = vector_scores.get("demand", 0)

        # Constitutional checks
        if feasibility < 20:
            # Too risky, regardless of demand
            return ("IGNORE", "IGNORE", "Do not pursue. Feasibility is catastrophically low.")
        
        if overall_score >= 80:
            return ("BUILD", "BUILD_NOW", "Generate MVP Plan and begin execution.")
        elif overall_score >= 60:
            if demand >= 70:
                msg = "High demand compensates for lower overall score. Build MVP."
                return ("BUILD", "BUILD_NOW", msg)
            else:
                msg = "Create a landing page or survey to validate demand."
                return ("VALIDATE", "VALIDATE_WITH_USERS", msg)
        elif overall_score >= 40:
            return ("WATCH", "WAIT_FOR_SIGNAL", "Set up alerts for competitor or market movement.")
        else:
            return ("IGNORE", "IGNORE", "Score is too low. Discard this opportunity.")
