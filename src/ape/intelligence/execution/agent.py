"""
ApeCoder Execution Agent.
(RFC-016)

LLM-driven task execution agent for governed code generation and execution steps.
Enforces strict canonical action vocabulary, MVP action restrictions, and max repair attempt bounds.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ape.intelligence.execution.models import ExecutionTask
from ape.intelligence.execution.policy import CANONICAL_ACTIONS
from ape.intelligence.roadmap.llm import PlannerModel

# Actions explicitly restricted in RFC-016 MVP
MVP_RESTRICTED_ACTIONS: set[str] = {
    "git_push",
    "deploy",
    "external_api_write",
    "credential_exposure"
}

AGENT_STEP_SCHEMA = {
    "type": "object",
    "properties": {
        "thought": {
            "type": "string",
            "description": "Reasoning for the proposed action step."
        },
        "action": {
            "type": "string",
            "description": "Canonical action name to execute (e.g. create_file, modify_file, run_tests, read_file)."
        },
        "params": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
                "command": {"type": "string"}
            }
        }
    },
    "required": ["thought", "action"]
}


@dataclass
class AgentStepResult:
    attempt: int
    thought: str
    action: str
    params: Dict[str, Any]
    exit_code: int
    stdout: str
    stderr: str
    status: str  # "SUCCESS" | "FAILED" | "BLOCKED" | "REJECTED"


@dataclass
class AgentExecutionResult:
    task_id: str
    status: str  # "COMPLETED" | "FAILED" | "BLOCKED"
    attempts: int
    steps: List[AgentStepResult]
    error: Optional[str] = None


class ApeCoderAgent:
    """
    Governed LLM execution agent.
    Receives an ExecutionTask and proposes sandbox actions.
    Performs up to max_repair_attempts loops on failure.
    """

    def __init__(
        self,
        model: PlannerModel,
        max_repair_attempts: int = 3
    ) -> None:
        self._model = model
        self._max_repair_attempts = max_repair_attempts

    def execute_task(
        self,
        task: ExecutionTask,
        workspace_context: str = "",
        lineage: Optional[Dict[str, str]] = None,
        sandbox_executor: Optional[Any] = None
    ) -> AgentExecutionResult:
        """
        Executes a task autonomously with bounded repair iterations.
        """
        steps: List[AgentStepResult] = []
        lineage_info = lineage or {}
        decision_id = lineage_info.get("decision_id", "UNKNOWN")
        policy_decision = lineage_info.get("policy_decision", "UNKNOWN")

        system_prompt = (
            "You are ApeCoder, an autonomous AI software execution agent.\n"
            "Your job is to execute a given task step-by-step by proposing safe canonical actions.\n"
            "Allowed actions: " + ", ".join(sorted(CANONICAL_ACTIONS - MVP_RESTRICTED_ACTIONS)) + ".\n"
            "You MUST preserve decision_id and policy_decision lineage.\n"
            "Do NOT propose git_push, deploy, or external_api_write in MVP.\n"
            "Respond ONLY in valid JSON matching the schema."
        )

        last_error = ""

        for attempt in range(1, self._max_repair_attempts + 1):
            user_prompt = (
                f"Task ID: {task.task_id}\n"
                f"Task Description: {task.description}\n"
                f"Required Deliverables: {', '.join(task.deliverables)}\n"
                f"Lineage: decision_id={decision_id}, policy={policy_decision}\n"
                f"Attempt: {attempt} of {self._max_repair_attempts}\n"
                f"Workspace Context:\n{workspace_context}\n"
            )

            if last_error:
                user_prompt += f"\nPrevious Error / Failure:\n{last_error}\nFix the issue and propose the next action."

            try:
                raw_proposal = self._model.generate(user_prompt, system_prompt, AGENT_STEP_SCHEMA)
                thought = raw_proposal.get("thought", "")
                proposed_action = raw_proposal.get("action", "")
                params = raw_proposal.get("params", {})

                # 1. Canonical Action Check
                if proposed_action not in CANONICAL_ACTIONS:
                    error_msg = f"Rejected: Action '{proposed_action}' is not in Canonical Action Vocabulary."
                    steps.append(AgentStepResult(attempt, thought, proposed_action, params, -1, "", error_msg, "REJECTED"))
                    last_error = error_msg
                    continue

                # 2. MVP Restriction Check
                if proposed_action in MVP_RESTRICTED_ACTIONS:
                    error_msg = f"Blocked: Action '{proposed_action}' is restricted in RFC-016 MVP."
                    steps.append(AgentStepResult(attempt, thought, proposed_action, params, -1, "", error_msg, "BLOCKED"))
                    last_error = error_msg
                    continue

                # 3. Sandbox / Simulation Execution
                exit_code = 0
                stdout = f"[SIMULATED] Successfully executed {proposed_action}"
                stderr = ""

                if sandbox_executor:
                    try:
                        # Execute in real/mock sandbox
                        res = sandbox_executor.execute_command(
                            cmd=params.get("command") or f"echo {proposed_action}",
                            cwd="/workspace"
                        )
                        exit_code = res.exit_code
                        stdout = res.output
                        stderr = res.error
                    except Exception as e:
                        exit_code = -1
                        stderr = str(e)

                if exit_code == 0:
                    steps.append(AgentStepResult(attempt, thought, proposed_action, params, exit_code, stdout, stderr, "SUCCESS"))
                    return AgentExecutionResult(task.task_id, "COMPLETED", attempt, steps)
                else:
                    error_msg = stderr or f"Action failed with exit code {exit_code}"
                    steps.append(AgentStepResult(attempt, thought, proposed_action, params, exit_code, stdout, stderr, "FAILED"))
                    last_error = error_msg

            except Exception as e:
                error_msg = f"LLM Generation / Agent Error: {str(e)}"
                steps.append(AgentStepResult(attempt, "Error during generation", "none", {}, -1, "", error_msg, "FAILED"))
                last_error = error_msg

        return AgentExecutionResult(
            task_id=task.task_id,
            status="FAILED",
            attempts=self._max_repair_attempts,
            steps=steps,
            error=f"Task failed after {self._max_repair_attempts} attempts. Last error: {last_error}"
        )
