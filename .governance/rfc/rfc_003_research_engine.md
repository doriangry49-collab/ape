# RFC-003: Research Engine

## 1. Mission
Implement the second user-facing Intelligence capability of APE. The objective is to make `ape research` produce meaningful market and audience research reports, operating under a local-first, remote-optional mindset.

## 2. Constitutional Alignment
- **Local-first, Remote-optional:** Network calls must fallback gracefully to local mocks/fixtures. Pytest must run offline.
- **Evidence-first:** Focus on structured signals (pain points, market indicators) before layering LLM summarization.
- **Decision Quality:** Structured outputs saved in JSON/Markdown feed directly into future evaluation pipelines.

## 3. Scope & CLI
Implement `ape research "topic"` command which queries HN Algolia search.
Normalized `ResearchReport` model fields:
- `topic`
- `target_audience`
- `competitors`
- `pain_points`
- `market_signals`
- `risks`
- `confidence`
- `sources`
- `discussions`
- `suggested_mvp`
- `timestamp`

Produces:
- `.build/research/<topic_slug>.json`
- `.build/research/<topic_slug>.md`

## 4. Directory Layout
```
src/ape/intelligence/research/
├── __init__.py
├── models.py
├── engine.py
└── providers/
    ├── __init__.py
    ├── base.py
    ├── hackernews.py
    └── audience.py
```

## 5. Acceptance Criteria
- [ ] `ape research` successfully runs.
- [ ] HackerNews Algolia API integrated and queried.
- [ ] Offline fallback is fully tested.
- [ ] Outputs `.build/research/` JSON and MD artifacts.
- [ ] Deterministic reproducibility verified.
- [ ] pytest and ruff pass clean.
- [ ] `/docs/SPRINT_REVIEW.md` generated at the end of the sprint.
