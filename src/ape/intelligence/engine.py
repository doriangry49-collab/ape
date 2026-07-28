from __future__ import annotations

from ape.intelligence.models import Opportunity
from ape.intelligence.scanner.github import GitHubTrendingScanner
from ape.intelligence.scanner.hackernews import HackerNewsScanner
from ape.project import Project


class OpportunityEngine:
    """Coordinates all scanners and aggregates normalized opportunity results."""

    def __init__(self, project: Project) -> None:
        self._project = project
        self._scanners = [
            GitHubTrendingScanner(),
            HackerNewsScanner(),
        ]

    def run_scans(self) -> list[Opportunity]:
        """Run all registered scanners and return merged, sorted results."""
        all_opportunities: list[Opportunity] = []
        for scanner in self._scanners:
            results = scanner.scan()
            all_opportunities.extend(results)

        # Sort by score descending
        return sorted(all_opportunities, key=lambda o: o.score, reverse=True)
