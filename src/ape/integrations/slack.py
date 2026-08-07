"""
Slack Integration Engine — ORION-103 Reality Check Specification.
Broadcasts Quality OS release decisions to Slack channels with REAL HTTP delivery or SIMULATED mode.
"""

import json
from typing import Any, Dict, Optional
import urllib.request


class SlackNotifier:
    """Formats and sends Slack webhook notifications for APE release decisions."""

    def __init__(self, webhook_url: Optional[str] = None) -> None:
        self.webhook_url = webhook_url

    def build_release_payload(self, topic_slug: str, decision: str, confidence: float, commit_sha: str = "main") -> Dict[str, Any]:
        """Construct Slack Block Kit message payload for release decision."""
        color = "#10b981" if decision == "RELEASE" else "#ef4444"
        return {
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"APE Release Decision: {decision}",
                            },
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Topic:* {topic_slug}"},
                                {"type": "mrkdwn", "text": f"*Confidence:* {confidence:.2f}%"},
                                {"type": "mrkdwn", "text": f"*Commit SHA:* `{commit_sha[:7]}`"},
                            ],
                        },
                    ],
                }
            ]
        }

    def notify_release(self, topic_slug: str, decision: str, confidence: float) -> Dict[str, Any]:
        """Send formatted notification payload to Slack webhook."""
        payload = self.build_release_payload(topic_slug, decision, confidence)

        if self.webhook_url and self.webhook_url.startswith("https://hooks.slack.com/"):
            body = json.dumps(payload).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            req = urllib.request.Request(self.webhook_url, data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req) as resp:
                    return {"integration_mode": "REAL", "status": "DELIVERED", "code": resp.status}
            except Exception as exc:
                return {"integration_mode": "SIMULATED", "status": "FAILED", "error": str(exc)}

        return {"integration_mode": "SIMULATED", "status": "DRY_RUN", "payload": payload}
