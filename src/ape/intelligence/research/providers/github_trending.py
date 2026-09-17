from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from ape.intelligence.research.providers.base import BaseResearchProvider


class GitHubTrendingResearchProvider(BaseResearchProvider):
    """Gathers research signals from GitHub repositories using GitHub Search API."""

    def __init__(self, offline: bool = False) -> None:
        self._offline = offline

    def fetch_signals(self, topic: str) -> dict[str, Any]:
        if self._offline:
            return {
                "discussions": [],
                "pain_points": [],
                "market_signals": [f"Offline mode: no GitHub data for '{topic}'"],
                "competitors": [],
                "sources": ["GitHubTrending"],
                "status": "NO_DATA",
            }

        try:
            query_encoded = urllib.parse.quote(topic)
            url = f"https://api.github.com/search/repositories?q={query_encoded}&sort=stars&order=desc"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))

            items = data.get("items", [])
            total_count = data.get("total_count", len(items))

            discussions = []
            pain_points = set()
            market_signals = []
            competitors = []

            # Heuristic keywords for repository analysis
            pain_keywords = {
                "wrapper": "Thin wrapper / integration overhead around native APIs",
                "alternative": "Community seeking alternative implementations",
                "difficult": "Complex installation / build requirements",
                "slow": "Performance & latency concerns reported",
                "missing": "Feature gaps in official repositories",
            }

            for item in items[:5]:
                full_name = item.get("full_name") or item.get("name") or "unknown/repo"
                html_url = item.get("html_url") or f"https://github.com/{full_name}"
                stars = item.get("stargazers_count") or 0
                desc = item.get("description") or ""

                discussions.append({
                    "title": f"GitHub Repo: {full_name} ({stars} stars)",
                    "url": html_url,
                    "points": stars,
                })

                competitors.append(full_name)

                desc_lower = desc.lower()
                for kw, description in pain_keywords.items():
                    if kw in desc_lower:
                        pain_points.add(description)

            if len(items) > 0:
                top_repo = items[0].get("full_name", "unknown")
                top_stars = items[0].get("stargazers_count", 0)
                market_signals.append(
                    f"Found {total_count} GitHub repositories for '{topic}'"
                )
                market_signals.append(
                    f"Top repository '{top_repo}' reached {top_stars} stars"
                )
                status = "SUCCESS"
            else:
                market_signals.append(f"No repositories found on GitHub for '{topic}'")
                status = "NO_DATA"

            return {
                "discussions": discussions,
                "pain_points": list(pain_points),
                "market_signals": market_signals,
                "competitors": competitors,
                "sources": ["GitHubTrending"],
                "status": status,
            }

        except Exception as exc:
            return {
                "discussions": [],
                "pain_points": [],
                "market_signals": [f"GitHub search failed or unavailable for '{topic}'"],
                "competitors": [],
                "sources": ["GitHubTrending"],
                "status": "NO_DATA",
                "error": str(exc),
            }
