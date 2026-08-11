"""
Workspace Role-Based Access Control (RBAC) Engine — EPIC G6-2 Specification.
Enforces permissions across ADMIN, DEVELOPER, and AUDITOR roles.
"""

from typing import Dict, Set


class WorkspaceRBAC:
    """Workspace Role-Based Access Control Engine."""

    ROLE_PERMISSIONS: Dict[str, Set[str]] = {
        "ADMIN": {"read", "write", "archive", "manage_users", "release"},
        "DEVELOPER": {"read", "write", "execute_pipeline"},
        "AUDITOR": {"read", "inspect_evidence", "view_reports"},
    }

    def check_permission(self, role: str, action: str) -> bool:
        """Check if role has permission to execute action."""
        role_upper = role.strip().upper()
        allowed = self.ROLE_PERMISSIONS.get(role_upper, set())
        return action.lower() in allowed
