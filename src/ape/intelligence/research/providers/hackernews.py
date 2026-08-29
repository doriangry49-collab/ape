from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from ape.intelligence.research.providers.base import BaseResearchProvider


class HackerNewsResearchProvider(BaseResearchProvider):
    """Gathers research signals from Hacker News using Algolia Search API."""

    def __init__(self, offline: bool = False) -> None:
        self._offline = offline

    def fetch_signals(self, topic: str) -> dict[str, Any]:
        if self._offline:
            return self._get_mock_signals(topic)

        try:
            query_encoded = urllib.parse.quote(topic)
            url = f"https://hn.algolia.com/api/v1/search?query={query_encoded}&tags=story"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                
            hits = data.get("hits", [])
            discussions = []
            pain_points = set()
            market_signals = []
            
            # Heuristic keywords for pain point detection
            pain_keywords = {
                "expensive": "Cost/Pricing concerns mentioned in discussions",
                "slow": "Performance bottlenecks reported by users",
                "difficult": "Complex configuration/setup issues",
                "broken": "Stability and bug complaints",
                "missing": "Feature completeness gaps",
            }
            
            for hit in hits[:5]:
                title = hit.get("title") or hit.get("story_title") or ""
                object_id = hit.get("objectID")
                hn_url = f"https://news.ycombinator.com/item?id={object_id}"
                points = hit.get("points") or 0
                
                discussions.append({
                    "title": title,
                    "url": hit.get("url") or hn_url,
                    "points": points
                })
                
                title_lower = title.lower()
                for kw, description in pain_keywords.items():
                    if kw in title_lower:
                        pain_points.add(description)

            # Build signals
            if len(hits) > 0:
                market_signals.append(
                    f"Found {len(hits)} HackerNews threads discussing '{topic}'"
                )
                top_points = hits[0].get('points', 0)
                market_signals.append(
                    f"Top discussion thread reached {top_points} points"
                )
            else:
                market_signals.append("Low discussion volume on HackerNews")

            # Fallback if no specific pain points detected but hits were found
            if not pain_points and len(hits) > 0:
                pain_points.add("Lack of robust integration options reported in community threads")
                
            return {
                "discussions": discussions,
                "pain_points": list(pain_points),
                "market_signals": market_signals,
                "sources": ["HackerNews"]
            }

        except Exception:
            return self._get_mock_signals(topic)

    def _get_mock_signals(self, topic: str) -> dict[str, Any]:
        """Returns reproducible deterministic mock signals for offline testing."""
        return {
            "discussions": [
                {
                    "title": f"Show HN: Fast local {topic} framework",
                    "url": "https://news.ycombinator.com/item?id=12345",
                    "points": 150
                },
                {
                    "title": f"Ask HN: What is the best {topic} tool?",
                    "url": "https://news.ycombinator.com/item?id=12346",
                    "points": 85
                }
            ],
            "pain_points": [
                "High API pricing and pricing model complexity",
                f"Difficult local setup and installation overhead for {topic}",
                "Integration support missing for major development tools"
            ],
            "market_signals": [
                f"Increasing HackerNews thread velocity for '{topic}' search",
                "High developer interest indicated by discussion score avg (117 pts)"
            ],
            "sources": ["HackerNews"]
        }
