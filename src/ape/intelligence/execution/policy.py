"""
Execution Policy — standalone boundary object.

Maps action names to safety levels. Engine never contains policy logic.
Unknown actions default to REQUIRES_APPROVAL (safe-by-default principle).
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

_POLICY_TABLE: dict[str, str] = {
    # SAFE — auto-execute, no user gate
    "read_file":          "SAFE",
    "run_tests":          "SAFE",
    "create_file":        "SAFE",
    "git_diff":           "SAFE",
    # REQUIRES_APPROVAL — pause and ask user
    "modify_file":        "REQUIRES_APPROVAL",
    "git_commit":         "REQUIRES_APPROVAL",
    "git_push":           "REQUIRES_APPROVAL",
    "delete_file":        "REQUIRES_APPROVAL",
    "deploy":             "REQUIRES_APPROVAL",
    "external_api_write": "REQUIRES_APPROVAL",
    # FORBIDDEN — never execute
    "credential_exposure": "FORBIDDEN",
}

# Single source of truth for canonical action vocabulary
CANONICAL_ACTIONS: set[str] = {
    "create_file",
    "modify_file",
    "delete_file",
    "read_file",
    "run_tests",
    "git_diff",
    "git_commit",
    "git_push",
    "deploy",
    "external_api_write",
    "search",
    "analyze",
}


class ExecutionPolicy:
    """Classify an action name into a safety level.

    Returns one of: "SAFE" | "REQUIRES_APPROVAL" | "FORBIDDEN"
    Unknown actions default to REQUIRES_APPROVAL (fail-safe).
    """

    def classify(self, action: str) -> str:
        return _POLICY_TABLE.get(action, "REQUIRES_APPROVAL")


def validate_path_containment(project_root: Path, target_path: str | Path) -> Tuple[bool, str]:
    """
    Validates that target_path, when resolved relative to project_root,
    is strictly contained within project_root.
    Returns (is_valid, error_message).
    """
    try:
        from pathlib import Path
        root_resolved = project_root.resolve()
        p = Path(target_path)
        if p.is_absolute():
            target_resolved = p.resolve()
        else:
            target_resolved = (project_root / p).resolve()

        try:
            target_resolved.relative_to(root_resolved)
            return True, ""
        except ValueError:
            return False, f"Path traversal rejected: target path '{target_path}' resolves outside workspace root ({root_resolved})."
    except Exception as e:
        return False, f"Invalid path '{target_path}': {str(e)}"
