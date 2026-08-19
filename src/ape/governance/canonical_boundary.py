"""
CanonicalGovernanceBoundary — Central Governance Boundary for Action Semantics & High-Impact Enforcement.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Union

from ape.governance.authorization_extractor import (
    AuthorizationCategory,
    AuthorizationSignal,
)
from ape.governance.exceptions import GovernanceAuthorizationRequired


class ActionSemantic(str, Enum):
    CANONICAL_BRANCH_WRITE = "CANONICAL_BRANCH_WRITE"  # Protected main/production branch write, merge, push
    FORCE_MUTATION = "FORCE_MUTATION"                  # Force push, hard reset, rebase
    PRODUCTION_DEPLOY = "PRODUCTION_DEPLOY"            # Production deployment, release publish
    READ_ONLY_INSPECTION = "READ_ONLY_INSPECTION"      # Read-only status, test, lint, log, diff


class CanonicalGovernanceBoundary:
    """
    Central Canonical Governance Boundary.
    Enforces that high-impact ActionSemantics require valid EXPLICIT_DIRECT_HUMAN_COMMAND authorization signals.
    """

    @staticmethod
    def validate_action(
        semantic: Union[ActionSemantic, str],
        authorization_signal: Optional[AuthorizationSignal] = None,
        command_args: Optional[Union[List[str], str]] = None,
    ) -> bool:
        if isinstance(semantic, ActionSemantic):
            sem_str = semantic.value
        elif hasattr(semantic, "value"):
            sem_str = str(semantic.value)
        else:
            sem_str = str(semantic)

        # 1. READ_ONLY_INSPECTION actions pass freely without authorization check
        if sem_str == ActionSemantic.READ_ONLY_INSPECTION.value:
            return True

        # 2. High-impact semantics require EXPLICIT_DIRECT_HUMAN_COMMAND signal
        if sem_str in (
            ActionSemantic.CANONICAL_BRANCH_WRITE.value,
            ActionSemantic.FORCE_MUTATION.value,
            ActionSemantic.PRODUCTION_DEPLOY.value,
        ):
            if not authorization_signal or not authorization_signal.is_valid or authorization_signal.category != AuthorizationCategory.EXPLICIT_DIRECT_HUMAN_COMMAND:
                reason = (
                    authorization_signal.reason
                    if authorization_signal
                    else "Missing valid current-turn human authorization signal."
                )
                raise GovernanceAuthorizationRequired(
                    action_semantic=sem_str,
                    reason=reason,
                    details={
                        "category": authorization_signal.category.value if authorization_signal else "NONE",
                        "command_args": command_args,
                    },
                )

        return True

    @staticmethod
    def classify_command(cmd: Union[List[str], str]) -> ActionSemantic:
        """Classifies command string or arguments list into an ActionSemantic."""
        if isinstance(cmd, list):
            cmd_str = " ".join(cmd)
        else:
            cmd_str = str(cmd)

        cmd_lower = cmd_str.lower()

        # Force mutation checks
        if "--force" in cmd_lower or "force-with-lease" in cmd_lower or "reset --hard" in cmd_lower:
            return ActionSemantic.FORCE_MUTATION

        # Canonical branch write checks (git push origin main, git merge ... main)
        if "git push" in cmd_lower and ("main" in cmd_lower or "master" in cmd_lower or "production" in cmd_lower):
            return ActionSemantic.CANONICAL_BRANCH_WRITE
        if "git merge" in cmd_lower and ("main" in cmd_lower or "master" in cmd_lower):
            return ActionSemantic.CANONICAL_BRANCH_WRITE
        if "deploy" in cmd_lower and "prod" in cmd_lower:
            return ActionSemantic.PRODUCTION_DEPLOY

        # Read-only inspection commands (pytest, ruff, git status, git log, git diff, echo, python -m)
        return ActionSemantic.READ_ONLY_INSPECTION
