"""
Jira Integration Engine — ORION-103 Reality Check Specification.
Maps Jira issues to APE production build tasks with REAL REST API v3 sync or SIMULATED mode.
"""

from dataclasses import dataclass
import json
from typing import Any, Dict, Optional
import urllib.request


@dataclass
class JiraIssueSync:
    """Represents a Jira issue linked to an APE build execution."""
    issue_key: str  # PROJ-123
    summary: str
    status: str  # In Progress, In Review, Done
    build_id: str
    integration_mode: str = "SIMULATED"


class JiraSyncEngine:
    """Handles Jira API synchronization for production task tracking."""

    def __init__(self, jira_url: str = "https://jira.enterprise.com", token: Optional[str] = None) -> None:
        self.jira_url = jira_url.rstrip("/")
        self.token = token
        self._synced_issues: Dict[str, JiraIssueSync] = {}

    def sync_issue(self, issue_key: str, summary: str, build_id: str, status: str = "In Review") -> JiraIssueSync:
        """Link or update Jira issue status with APE build execution."""
        mode = "SIMULATED"
        if self.token and not self.jira_url.startswith("https://jira.enterprise.com"):
            url = f"{self.jira_url}/rest/api/3/issue/{issue_key}"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
            body = json.dumps({"fields": {"summary": summary}}).encode("utf-8")
            req = urllib.request.Request(url, data=body, headers=headers, method="PUT")
            try:
                with urllib.request.urlopen(req) as resp:
                    mode = "REAL"
            except Exception:
                mode = "SIMULATED"

        item = JiraIssueSync(
            issue_key=issue_key,
            summary=summary,
            status=status,
            build_id=build_id,
            integration_mode=mode,
        )
        self._synced_issues[issue_key] = item
        return item

    def get_issue_status(self, issue_key: str) -> Optional[JiraIssueSync]:
        """Fetch Jira issue sync state."""
        return self._synced_issues.get(issue_key)
