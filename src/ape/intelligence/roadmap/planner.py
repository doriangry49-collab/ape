"""
Intelligent Planner that coordinates the LLM model and generates proposals.
(RFC-015)
"""
from ape.intelligence.roadmap.contracts import PLANNER_PROPOSAL_SCHEMA, PlannerProposal
from ape.intelligence.roadmap.llm import PlannerModel


class IntelligentPlanner:
    def __init__(self, model: PlannerModel):
        self._model = model

    def generate_proposal(
        self, 
        topic: str,
        decision_id: str, 
        policy_decision: str, 
        evidence_context: str
    ) -> PlannerProposal:
        """
        Generates a structured roadmap proposal from the LLM.
        Raises RuntimeError if LLM fails or returns invalid schema.
        """
        system_message = (
            "You are an expert autonomous AI project planner. "
            "Your task is to propose a structured roadmap of milestones and tasks based on the provided evidence and policy decision. "
            "You MUST preserve the provided decision_id and policy_decision EXACTLY. "
            "Do NOT include arbitrary shell execution commands in task actions. Use semantic actions like 'create_file', 'modify_file', 'analyze', 'search'. "
            "If the policy is BUILD, focus on software development milestones. "
            "If the policy is VALIDATE, focus on market validation and signal testing milestones. "
        )

        prompt = (
            f"Topic: {topic}\n"
            f"Decision ID: {decision_id}\n"
            f"Policy Decision: {policy_decision}\n"
            f"Evidence Context:\n{evidence_context}\n\n"
            "Generate the roadmap proposal."
        )

        raw_result = self._model.generate(prompt, system_message, PLANNER_PROPOSAL_SCHEMA)
        
        # We parse it into our internal contract model
        return PlannerProposal.from_dict(raw_result)
