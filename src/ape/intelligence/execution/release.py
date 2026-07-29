"""
Governed Commit & Staging Boundary (ReleaseGate).
(RFC-018)

Bridges completed ExecutionState results with repository git history under strict governance.
Ensures post-execution quality checks, lineage-embedded commit messages, and human approval gates.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from ape.intelligence.execution.models import ExecutionState, ExecutionStatus
from ape.intelligence.execution.policy import ExecutionPolicy
from ape.utils import append_to_evidence, get_artifact_history


@dataclass
class ReleaseProposal:
    execution_id: str
    decision_id: str
    policy_decision: str
    evidence_hash: str
    topic_slug: str
    changed_files: List[str]
    commit_message: str
    quality_check_passed: bool
    quality_errors: List[str]


class ReleaseGate:
    """
    Governed release gate that converts completed ExecutionState outputs
    into audited, policy-approved git commits with embedded decision lineage.
    """

    def __init__(self, project_root: Path, policy: Optional[ExecutionPolicy] = None):
        self._root = project_root
        self._policy = policy or ExecutionPolicy()

    def prepare_release(self, topic_slug: str) -> ReleaseProposal:
        """
        Inspects execution state, verifies quality pre-checks, and builds a release proposal.
        Raises FileNotFoundError if execution state artifact is missing.
        """
        state_file = self._root / ".build" / "execution" / topic_slug / "current.json"
        if not state_file.exists():
            raise FileNotFoundError(f"Execution state not found for: {topic_slug}")

        state_data = json.loads(state_file.read_text(encoding="utf-8"))
        state = ExecutionState.from_dict(state_data)

        # 1. Lineage & Policy Gate Check
        if state.policy_decision not in ("BUILD", "VALIDATE"):
            raise ValueError(
                f"Cannot release execution with policy_decision '{state.policy_decision}'. "
                "Only BUILD or VALIDATE executions may be released."
            )

        # 2. Execution Completion Check
        if state.status != ExecutionStatus.COMPLETED:
            raise ValueError(
                f"Execution for '{topic_slug}' is not COMPLETED (current status: {state.status.value})."
            )

        # 3. Quality Pre-check (Syntax validation on python deliverables)
        changed_files = self._get_git_changed_files()
        quality_passed, quality_errors = self._run_quality_precheck(changed_files)

        # 4. Generate Lineage-Embedded Commit Message
        commit_msg = (
            f"feat(execution): [{topic_slug}] complete execution {state.execution_id}\n\n"
            f"- Decision ID: {state.decision_id}\n"
            f"- Policy: {state.policy_decision}\n"
            f"- Evidence Hash: {state.evidence_hash}\n"
            f"- Execution ID: {state.execution_id}"
        )

        return ReleaseProposal(
            execution_id=state.execution_id,
            decision_id=state.decision_id,
            policy_decision=state.policy_decision,
            evidence_hash=state.evidence_hash,
            topic_slug=topic_slug,
            changed_files=changed_files,
            commit_message=commit_msg,
            quality_check_passed=quality_passed,
            quality_errors=quality_errors,
        )

    def execute_release(self, proposal: ReleaseProposal, user_approved: bool) -> bool:
        """
        Executes git staging and commit if quality check passes and human approval is granted.
        Emits release event to .governance/evidence/release-YYYY-MM.jsonl.
        """
        evidence_dir = self._root / ".governance" / "evidence"

        # Check ExecutionPolicy for git_commit
        safety = self._policy.classify("git_commit")
        if safety == "FORBIDDEN":
            self._emit_release_event(evidence_dir, proposal, "FORBIDDEN", "git_commit forbidden by policy")
            return False

        if not proposal.quality_check_passed:
            self._emit_release_event(evidence_dir, proposal, "REJECTED", f"Quality check failed: {proposal.quality_errors}")
            return False

        if not user_approved:
            self._emit_release_event(evidence_dir, proposal, "DENIED", "User denied release approval")
            return False

        # Execute Git Staging & Commit
        try:
            # Stage changed files
            for file_path in proposal.changed_files:
                subprocess.run(
                    ["git", "add", file_path],
                    cwd=self._root,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            # Create commit
            subprocess.run(
                ["git", "commit", "-m", proposal.commit_message],
                cwd=self._root,
                check=True,
                capture_output=True,
                text=True,
            )

            self._emit_release_event(evidence_dir, proposal, "COMMITTED", "Commit created successfully")
            return True

        except subprocess.CalledProcessError as e:
            err_msg = e.stderr or str(e)
            self._emit_release_event(evidence_dir, proposal, "FAILED", f"Git commit failed: {err_msg}")
            return False

    def _get_git_changed_files(self) -> List[str]:
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self._root,
                capture_output=True,
                text=True,
                check=True,
            )
            files = []
            for line in res.stdout.strip().split("\n"):
                if line.strip():
                    # Format: XY path or XY "path"
                    parts = line.strip().split(maxsplit=1)
                    if len(parts) == 2:
                        files.append(parts[1].strip('"'))
            return files
        except Exception:
            return []

    def _run_quality_precheck(self, files: List[str]) -> Tuple[bool, List[str]]:
        errors = []
        for file_path in files:
            full_path = self._root / file_path
            if full_path.suffix == ".py" and full_path.exists():
                try:
                    import sys
                    res = subprocess.run(
                        [sys.executable, "-m", "py_compile", str(full_path)],
                        capture_output=True,
                        text=True,
                    )
                    if res.returncode != 0:
                        errors.append(f"Syntax error in {file_path}: {res.stderr}")
                except Exception as e:
                    errors.append(f"Quality check error for {file_path}: {str(e)}")
        return (len(errors) == 0), errors

    def _emit_release_event(self, evidence_dir: Path, proposal: ReleaseProposal, status: str, details: str) -> None:
        payload = {
            "topic_slug": proposal.topic_slug,
            "execution_id": proposal.execution_id,
            "decision_id": proposal.decision_id,
            "policy_decision": proposal.policy_decision,
            "evidence_hash": proposal.evidence_hash,
            "status": status,
            "details": details,
            "changed_files": proposal.changed_files,
            "commit_message": proposal.commit_message,
        }
        append_to_evidence(evidence_dir, "release", payload)
