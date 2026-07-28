"""
Execution Policy — standalone boundary object.

Maps action names to safety levels. Engine never contains policy logic.
Unknown actions default to REQUIRES_APPROVAL (safe-by-default principle).
"""
from __future__ import annotations

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


class ExecutionPolicy:
    """Classify an action name into a safety level.

    Returns one of: "SAFE" | "REQUIRES_APPROVAL" | "FORBIDDEN"
    Unknown actions default to REQUIRES_APPROVAL (fail-safe).
    """

    def classify(self, action: str) -> str:
        return _POLICY_TABLE.get(action, "REQUIRES_APPROVAL")
