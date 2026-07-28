# Skill: Evidence & Audit Trail (Hafıza)

Evidence is APE's permanent memory (hafıza). It records the history of actions, research, decisions, and execution outcomes.

## Core Evidence Principles
1. **Append-Only:** Evidence is strictly append-only. Write new rows to `.governance/evidence/*.jsonl`; never modify or truncate existing lines.
2. **Persistence:** Evidence is NOT a transient runtime cache. It must survive clean builds, new AI sessions, and fresh repository clones.
3. **No Silent Deletion:** No AI agent or automated script may delete, truncate, or alter evidence files without explicit human approval.

---

## State vs. Evidence Separation

| Type | Directory | Mutability | Reading Method |
|---|---|---|---|
| **CURRENT STATE** | `.build/` | Mutable (Overwritten) | O(1) canonical file path (e.g. `ai_agents.json`) |
| **EVIDENCE** | `.governance/evidence/` | Immutable (Append-Only) | Stream reading from JSONL log files |

This separation ensures high-performance downstream reads (O(1) state lookup) while preserving absolute traceability.
