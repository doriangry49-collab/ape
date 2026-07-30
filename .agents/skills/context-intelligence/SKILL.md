---
name: context-intelligence
description: Guidance for targeted symbol and section retrieval to minimize context consumption.
---

# Context Intelligence Protocol

## 1. Principles & Priority
Priority Hierarchy: Correctness > Sufficient Evidence > Minimal Context > Speed.

## 2. Routing Rules
- **Python Source (.py):** Use `jCodeMunch` (`get_symbol`, `search_symbols`).
- **Docs & SPECs (.md):** Use `jDocMunch` (`get_section`, `get_outline`).
- **Small Files (<50 lines):** Use native `view_file` directly.
- **Trivial Edits / New Files:** Use native `view_file` or `write_to_file`.

## 3. Retrieval Execution & Lazy Expansion
- Use native MCP tool calls directly. **DO NOT** execute MCP commands via terminal shell (`run_command`).
- **Lazy L1 Scope:** Retrieve target symbol/section only (Level 1). Do NOT eagerly expand to Level 2/3 references unless Level 1 evidence is incomplete.
- **Stopping Rule:** Stop retrieval immediately once target invariant, function contract, or test assertion is verified.

## 4. Fallback Chain
If an MCP tool fails, times out, or symbol/section is not found:
1. `grep_search` (Ripgrep pattern search)
2. Bounded `view_file` (Line range view)
3. Full-file `view_file` (Last resort)
