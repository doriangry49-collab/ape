from __future__ import annotations

import json
import urllib.request
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from ape.intelligence.models import Opportunity
from ape.intelligence.scanner.adapters.web_search_adapter import AdapterError
from ape.intelligence.scanner.base import BaseScanner
from ape.intelligence.scoring import calculate_heuristic_score


class HackerNewsScanner(BaseScanner):
    """Scans and retrieves top stories from Hacker News."""

    def scan(self) -> list[Opportunity]:
        opportunities = []
        try:
            # Fetch top stories list
            req = urllib.request.Request(
                "https://hacker-news.firebaseio.com/v0/topstories.json",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                top_ids = json.loads(response.read().decode())[:5]

            # Fetch details for the top 5
            for item_id in top_ids:
                try:
                    item_req = urllib.request.Request(
                        f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json",
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    with urllib.request.urlopen(item_req, timeout=3) as item_response:
                        item_data = json.loads(item_response.read().decode())
                        
                    title = item_data.get("title", "")
                    score_pts = item_data.get('score', 0)
                    author = item_data.get('by', '')
                    description = (
                        f"HN Score: {score_pts} points. Author: {author}"
                    )
                    url = item_data.get(
                        "url",
                        f"https://news.ycombinator.com/item?id={item_id}"
                    )
                    score_val = item_data.get("score", 0)
                    time_val = item_data.get("time", 0)

                    now = datetime.now(UTC)
                    if time_val:
                        published_at = datetime.fromtimestamp(time_val, UTC)
                    else:
                        published_at = now
                    age_hours = (now - published_at).total_seconds() / 3600.0
                    
                    calc_score, confidence = calculate_heuristic_score(score_val, age_hours, title)
                    
                    opportunities.append(Opportunity(
                        title=title,
                        description=description,
                        url=url,
                        source="HackerNews",
                        score=calc_score,
                        confidence=confidence,
                        published_at=published_at,
                        tags=["hackernews", "trending"]
                    ))
                except Exception:
                    continue
        except Exception as e:
            # SPEC-0012: ERROR != UNKNOWN. Propagate AdapterError without synthetic evidence.
            raise AdapterError(f"HackerNews scan failed: {e}") from e

        return opportunities
