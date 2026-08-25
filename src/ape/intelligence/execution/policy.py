"""
Execution Policy — standalone boundary object.

Maps action names to safety levels. Engine never contains policy logic.
Unknown actions default to REQUIRES_APPROVAL (safe-by-default principle).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Tuple

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

# Constitutional Typed Parameter Schemas per Action
ACTION_PARAMETER_SCHEMAS: dict[str, dict[str, dict[str, type]]] = {
    "create_file": {
        "required": {"path": str, "content": str},
        "optional": {},
    },
    "modify_file": {
        "required": {"path": str, "content": str},
        "optional": {},
    },
    "read_file": {
        "required": {"path": str},
        "optional": {},
    },
    "run_tests": {
        "required": {},
        "optional": {"target": str},
    },
    "delete_file": {
        "required": {"path": str},
        "optional": {},
    },
    "git_diff": {
        "required": {},
        "optional": {"path": str},
    },
    "git_commit": {
        "required": {"message": str},
        "optional": {},
    },
    "git_push": {
        "required": {},
        "optional": {"remote": str, "branch": str},
    },
    "deploy": {
        "required": {"environment": str},
        "optional": {},
    },
}


def validate_action_parameters(action: str, params: dict[str, Any]) -> Tuple[bool, str]:
    """
    Constitutional parameter schema validation.
    Enforces strict typing, required keys presence, and REJECTS extraneous parameter keys.
    """
    if action not in CANONICAL_ACTIONS:
        return False, f"UNKNOWN_CANONICAL_ACTION: Action '{action}' is not in Canonical Action Vocabulary."

    schema = ACTION_PARAMETER_SCHEMAS.get(action)
    if schema is None:
        # Action is canonical but unconstrained by explicit parameter schema (e.g. search, analyze)
        return True, ""

    required_spec = schema.get("required", {})
    optional_spec = schema.get("optional", {})
    allowed_keys = set(required_spec.keys()).union(optional_spec.keys())

    # Check for extraneous keys (e.g. command injection attempt)
    extraneous = set(params.keys()) - allowed_keys
    if extraneous:
        return (
            False,
            f"PARAMETER_SCHEMA_VIOLATION: Action '{action}' contains unauthorized parameter keys: {sorted(extraneous)}. "
            f"Allowed keys: {sorted(allowed_keys)}"
        )

    # Check required keys
    missing_required = set(required_spec.keys()) - set(params.keys())
    if missing_required:
        return (
            False,
            f"PARAMETER_SCHEMA_VIOLATION: Action '{action}' missing required parameters: {sorted(missing_required)}."
        )

    # Type check provided keys
    all_specs = {**required_spec, **optional_spec}
    for k, val in params.items():
        expected_type = all_specs.get(k)
        if expected_type and not isinstance(val, expected_type):
            return (
                False,
                f"PARAMETER_TYPE_VIOLATION: Action '{action}' parameter '{k}' expected type {expected_type.__name__}, got {type(val).__name__}."
            )

    return True, ""



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

def translate_sandbox_path(path: str) -> str:
    """
    Translates a sandbox namespace path (e.g., /workspace/foo.py) into a host-relative candidate.
    Does NOT resolve traversals or validate security - simply strips the sandbox namespace prefix
    so the host containment guard can evaluate the true intent.
    """
    if path.startswith("/workspace/"):
        return path[11:]
    elif path.startswith("\\workspace\\"):
        return path[11:]
    elif path.startswith("/workspace\\"):
        return path[11:]
    elif path.startswith("\\workspace/"):
        return path[11:]
    elif path == "/workspace" or path == "\\workspace":
        return "."
    return path
