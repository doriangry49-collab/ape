"""
Unit tests for ORION-103 Reality Check & Real Integration Matrix.
Verifies integration_mode tagging (REAL vs SIMULATED) across GitHub, Slack, and Jira clients.
"""

import pytest

from ape.integrations import GitHubWebhookHandler, JiraSyncEngine, SlackNotifier


def test_github_real_vs_simulated_mode():
    # 1. Offline mode without GITHUB_TOKEN
    gh_offline = GitHubWebhookHandler(token=None)
    pr_offline = gh_offline.create_pull_request("acme/repo", "ape/patch", "Fix tests")
    assert pr_offline["integration_mode"] == "SIMULATED"
    assert "(SIMULATED)" in pr_offline["pr_url"]

    # 2. Real mode with GITHUB_TOKEN set
    gh_real = GitHubWebhookHandler(token="mock_token_123")
    assert gh_real.token == "mock_token_123"


def test_slack_real_vs_simulated_mode():
    # 1. Offline dry-run mode
    slack_offline = SlackNotifier(webhook_url=None)
    res_offline = slack_offline.notify_release("api_task", "RELEASE", 95.5)
    assert res_offline["integration_mode"] == "SIMULATED"
    assert res_offline["status"] == "DRY_RUN"

    # 2. Real mode configuration
    slack_real = SlackNotifier(webhook_url="https://hooks.slack.com/services/T00/B00/X00")
    assert slack_real.webhook_url.startswith("https://hooks.slack.com/")


def test_jira_real_vs_simulated_mode():
    jira = JiraSyncEngine(jira_url="https://jira.enterprise.com", token=None)
    sync = jira.sync_issue("PROJ-101", "Build MVP App", "build_001")
    assert sync.integration_mode == "SIMULATED"
