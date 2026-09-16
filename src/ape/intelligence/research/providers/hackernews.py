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
            return {
                "discussions": [],
                "pain_points": [],
                "market_signals": [f"Offline mode: no HackerNews data for '{topic}'"],
                "sources": ["HackerNews"],
                "status": "NO_DATA",
            }

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
                status = "SUCCESS"
            else:
                market_signals.append(f"Low discussion volume on HackerNews for '{topic}'")
                status = "NO_DATA"

            return {
                "discussions": discussions,
                "pain_points": list(pain_points),
                "market_signals": market_signals,
                "sources": ["HackerNews"],
                "status": status,
            }

        except Exception as exc:
            return {
                "discussions": [],
                "pain_points": [],
                "market_signals": [f"HackerNews search failed or unavailable for '{topic}'"],
                "sources": ["HackerNews"],
                "status": "NO_DATA",
                "error": str(exc),
            }
