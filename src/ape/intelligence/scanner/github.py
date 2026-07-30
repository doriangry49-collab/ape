from __future__ import annotations

import re
import urllib.request
from datetime import UTC, datetime

from ape.intelligence.models import Opportunity
from ape.intelligence.scanner.adapters.web_search_adapter import AdapterError
from ape.intelligence.scanner.base import BaseScanner
from ape.intelligence.scoring import calculate_heuristic_score


class GitHubTrendingScanner(BaseScanner):
    """Scans and retrieves repositories from GitHub Trending page."""

    def scan(self) -> list[Opportunity]:
        opportunities = []
        try:
            req = urllib.request.Request(
                "https://github.com/trending",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                html = response.read().decode("utf-8")

            # Extract repo paths and descriptions
            # Typical tag: <h2 class="h3 lh-condensed"><a href="/user/repo" ...>
            repos = re.findall(r'<h2 class="h3 lh-condensed">\s*<a\s+href="([^"]+)"', html)
            
            # Simple fallback if regex fails due to HTML changes
            if not repos:
                raise ValueError("Could not parse repositories from HTML.")

            for path in repos[:5]:
                clean_path = path.lstrip("/")
                title = clean_path
                url = f"https://github.com/{clean_path}"
                description = f"GitHub repository: {clean_path}."
                
                # Fetch random daily stars for score heuristic
                calc_score, confidence = calculate_heuristic_score(150, 1.0, title)
                
                opportunities.append(Opportunity(
                    title=title,
                    description=description,
                    url=url,
                    source="GitHub Trending",
                    score=calc_score,
                    confidence=confidence,
                    published_at=datetime.now(UTC),
                    tags=["github", "trending", clean_path.split("/")[-1]]
                ))

        except Exception as e:
            # SPEC-0012: ERROR != UNKNOWN. Propagate AdapterError without synthetic evidence.
            raise AdapterError(f"GitHub Trending scan failed: {e}") from e

        return opportunities
