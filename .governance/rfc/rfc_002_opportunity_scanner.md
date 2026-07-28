# RFC-002: Opportunity Scanner MVP

## 1. Mission
Implement the first user-facing Intelligence capability of APE. The objective is to make `ape scan` produce meaningful market opportunities.

## 2. Constitutional Alignment
This sprint complies with APE Product Vision v1.1:
- Zero architecture bloat.
- Core is frozen.
- Purely additive functionality in `src/ape/intelligence/`.

## 3. Scope & CLI
Implement `ape scan` CLI command collecting opportunities from:
- GitHub Trending
- Hacker News

Every result is normalized into a unified `Opportunity` model:
- `title`
- `description`
- `url`
- `source`
- `score`
- `confidence`
- `published_at`
- `tags`

## 4. Architecture
```
src/ape/intelligence/
├── __init__.py
├── models.py
├── engine.py
├── scoring.py
└── scanner/
    ├── __init__.py
    ├── base.py
    ├── github.py
    └── hackernews.py
```

## 5. Scoring heuristics
For the MVP, we use simple heuristics (stars, score, age) to output:
- `score` (0-100)
- `confidence` (0.0-1.0)
No LLM required yet.

## 6. Acceptance Criteria
- [ ] `ape scan` runs successfully.
- [ ] At least two providers work (GitHub, HackerNews).
- [ ] Output normalized.
- [ ] Tests pass (pytest, ruff, validate).
- [ ] `/docs/SPRINT_REVIEW.md` generated at the end of the sprint.
