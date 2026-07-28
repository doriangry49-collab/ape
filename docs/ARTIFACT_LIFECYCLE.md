# Artifact Lifecycle & Immutability Rules

To maintain absolute data integrity and prevent corruption, APE enforces the **Immutable Artifacts Principle**.

> **Architectural Rule:** No sprint may introduce a new artifact unless its lifecycle is explicitly defined.

## Principle of Immutability
Artifacts under `.build/` must NEVER be overwritten. When a process runs again, it must generate a new file, usually suffixed with a timestamp (e.g., `ai_agents_1701234567.json`). Consumers of these artifacts must always read the latest chronologically generated file for a given topic slug.

---

## Defined Artifact Lifecycles

### 1. Research Report
- **Owner:** `ResearchEngine` (`ape research`)
- **Source:** External network providers (HackerNews, Reddit, GitHub, etc.)
- **Destination:** `.build/research/<slug>_<timestamp>.json` and `.md`
- **Version:** `1.0`
- **Retention:** Permanent. Older versions serve as historical snapshots of market data.

### 2. Decision Report
- **Owner:** `DecisionEngine` (`ape decide`)
- **Source:** Latest `ResearchReport` for the topic
- **Destination:** `.build/decisions/<slug>_<timestamp>.json` and `.md`
- **Evidence Append:** Must also append the JSON payload to `.governance/evidence/decisions.jsonl`
- **Version:** `1.0`
- **Retention:** Permanent. Critical for the Evolution Track to trace decision paths.

### 3. Execution Roadmap
- **Owner:** `RoadmapGenerator` (`ape plan`)
- **Source:** Latest `DecisionReport` for the topic
- **Destination:** `.build/roadmaps/<slug>_<timestamp>.json` and `.md`
- **Version:** `1.0`
- **Retention:** Permanent. Serves as the blueprint for development execution.
