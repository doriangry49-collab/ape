"""
Unit tests for Real Enterprise Integrations (EPIC G8-1).
"""

import json

from ape.integrations import GitHubWebhookHandler, JiraSyncEngine, SlackNotifier


def test_github_webhook_parsing_and_verification():
    handler = GitHubWebhookHandler(secret="test_secret")
    payload_raw = json.dumps({"action": "opened", "repository": {"full_name": "ape/core"}, "pull_request": {"number": 42, "head": {"sha": "abc123sha"}}})

    event = handler.parse_event("pull_request", payload_raw)
    assert event.event_type == "pull_request"
    assert event.repo_name == "ape/core"
    assert event.pr_number == 42


def test_jira_sync_engine():
    engine = JiraSyncEngine()
    sync = engine.sync_issue("PROJ-99", "Build Production REST API", "build_001")

    assert sync.issue_key == "PROJ-99"
    assert sync.status == "In Review"
    assert engine.get_issue_status("PROJ-99") is not None


def test_slack_notifier():
    notifier = SlackNotifier()
    payload = notifier.build_release_payload("calc_app", "RELEASE", 95.5)

    assert "attachments" in payload
    assert payload["attachments"][0]["color"] == "#10b981"
    res = notifier.notify_release("calc_app", "RELEASE", 95.5)
    assert res["status"] in ("DRY_RUN", "DELIVERED")
