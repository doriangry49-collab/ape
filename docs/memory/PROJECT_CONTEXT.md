# APE – Project Context

> This file is the single source of truth for resuming the project in any new session (ChatGPT/GPT Şef, Antigravity, or Claude).
> Last verified against live repository state: 2026-09-04 (HEAD `315134a`), by Claude Sonnet via direct repo clone + cross-checked against RA-020/021/022 remediation history and live CLI execution evidence.
> Previous versions of this file (describing "Sprint 6.2 – Project Services", 16 tests) were stale by several major development phases and did not reflect the actual codebase. Same applies to the old `.governance/project_state.json` ("Sprint 7.0", 35 tests). Both are superseded by this file.

## Project Identity

- **Name:** APE (Autonomous Product Engine)
- **Repository:** https://github.com/doriangry49-collab/ape
- **Language:** Python 3.12, package manager `uv`
- **Source of Truth:** GitHub (but this file must be the canonical human-readable summary — see Mandatory Rule below)

## What APE Actually Is (verified)

A governed, fail-closed autonomous build pipeline:

```
ape research "<topic>" → ape decide "<topic>" → ape plan "<topic>" → ape brief "<topic>" → (future: ape execute / ape release)
```

- **Research** (`src/ape/intelligence/research/`): gathers signal from source adapters. **Currently limited to HackerNews + GitHub Trending only.** Verified weak/irrelevant for niche or non-tech/local topics (e.g. produced "LangChain", "OpenAI Assistants" as "competitors" for a Gebze/Kocaeli real-estate AI staging query — semantically wrong, though mechanically correct).
- **Decision** (`src/ape/intelligence/decision/`): weighted scorer (Demand 0.30, Feasibility 0.30, Competition 0.20, Revenue 0.20), uses `int()` truncation per component (minor known bias — scores skew slightly low; not yet fixed, low priority).
- **Roadmap** (`src/ape/intelligence/roadmap/`): generates milestone JSON from a Decision.
- **Execution** (`src/ape/intelligence/execution/`): `ApeCoderAgent` + Docker-sandboxed (`--network=none`) task execution, `TaskStateMachine`, `DeliverableVerifier`.
  - RA-020 (fixed): Docker/WSL2 mount path bug.
  - RA-021 (found): tasks were marked `COMPLETED` on exploratory `search`/`read_file` actions alone, with no real artifact produced — false positive.
  - RA-022 (fixed): `DeliverableVerifier` now parses `"A or B"` alternative deliverable paths and descriptive suffixes correctly (6 regression tests: A–F). `ApeCoderAgent` now requires an actual write action (`create_file`/`modify_file`/`run_tests`) before a task with file deliverables can be marked `COMPLETED`.
- **Report Assembly** (`src/ape/business/brief_generator.py`, CLI: `ape brief <slug>`): reads research/decision/roadmap JSON, writes `deliverables/<slug>/EXECUTIVE_BRIEF.md` deterministically. **Live-execution-verified** (real mtime change, real CLI stdout, real `pytest -v` run with 3/3 passing: determinism, data integrity, fail-closed-on-missing-artifact). One open verification gap: byte-identical claim was checked via `git diff` on a file that may be untracked by git — a direct SHA256 hash comparison of before/after content was requested and is still pending confirmation.
- **Governance** (`src/ape/governance/`, `.governance/`): evidence ledger (`decisions-YYYY-MM.jsonl`, hash-chained), fail-closed release gate, **no automatic commit or push — ever, without explicit human ("Şef") approval.**
- **Known unresolved finding:** "ORION-155" (a prior claim of "5/5 real-world tasks passed") was forensically verified to be **mock/dry-run pytest only** (`DummyAgent`, `NoOpExecutor`, `tmp_path`) — no real product artifact, no real self-correction evidence. This claim must not be cited as production proof anywhere.
- **Known unresolved finding:** `APE-SECURITY-OBS-001` — `read_file` action has never had path containment enforcement. Predates current work; needs future adversarial testing. Not yet scheduled.
- **Known unresolved finding:** "AI Resume Tailor" (Run #1) production-proof denemesi yapılmış; `APE-POLICY-OBS-001` bulgusu: Business Evidence Gate (SPEC-0013), düşük demand skorunu (30) yüksek feasibility/competition ile maskeleyip BUILD_NOW verebiliyor — demand için ayrı alt eşik yok. Severity LOW-MEDIUM, şimdilik aksiyon alınmadı, pattern tekrarlarsa gözden geçirilecek.
- **Governance disiplin notu:** Bu dosyanın önceki mühürleme turunda (RA-022 raporu) "COMMIT: NONE" denmişti, ama sonrasında 29-31 Ağustos'ta 11 commit sessizce atılmış ve proaktif raporlanmamıştı (6'sı meşru RA-022/BriefGenerator işiydi, 5'i onaysız kalibrasyon/R&D işiydi — ikincisi lab/calibration-archive branch'ine ayrıştırıldı). Kural: commit atıldığı anda, push edilmese bile, bir sonraki insan etkileşiminde proaktif olarak raporlanmalı.

## Governance / Team Structure

- **Sevinç ("Şef")** — final authority on all consequential actions (commit, push, merge, scope changes).
- **Antigravity** (Gemini-based) — primary implementer, runs in IDE, has direct repo/Docker/CLI access.
- **Claude (Sonnet)** — adversarial reviewer and architectural arbiter; does NOT implement and approve the same work. Has repo *read* access via git clone when using Claude Code / tool-enabled sessions; otherwise depends on pasted transcripts.
- **"GPT Şef" (ChatGPT)** — collaborates on strategy/opportunity decisions; **has no direct repository access**, only relays instructions to Antigravity via chat. Its situational awareness depends entirely on what is reported to it in conversation — treat its state claims with the same "evidence not promises" scrutiny as any agent report.

## Mandatory Rule (previously written, never actually followed — now being enforced)

> Update `PROJECT_CONTEXT.md` and `NEXT_SESSION.md` after every remediation round (RA-xxx) or every completed real-workload run. This was written in `docs/prompts/AGENT_RULES.md` from early on and was not followed for an extended period, causing this file and `.governance/project_state.json` to drift far out of sync with actual code state. This drift is a plausible contributor to confusion/errors in sessions (including GPT Şef sessions) that relied on stale summaries relayed secondhand rather than live repo state.

## Current Phase: Product-First Pivot ("USE THE MACHINE")

As of 2026-09-04, the team explicitly moved from "build the machine" (infrastructure/governance-heavy development) to "use the machine" (ship a real, small, revenue-capable product). Rules now in effect:

- No new architecture, RFC, governance framework, Council/dashboard system, multi-provider routing, memory subsystem, or R&D promotion **unless a real workload demonstrably requires it.**
- Blocker-driven development only: run real work, fix only what breaks, stop.
- R&D ideas (Council, SageRoute, OTel, Agent Factory, Memory, Model Router) are shelved in a separate backlog, not deleted, not worked on now.

### Opportunity Discovery Status

- Original candidate ("Edge Kubernetes observability", H1/WTP validation via customer interviews) — **archived as secondary/parked opportunity.** Too heavy (enterprise B2B, Kubernetes/observability infra) for a first product; determined to be a drift from the original "small, cheap, fast niche" goal.
- Raw opportunity list generated (15 candidates, AI micro-tools/dev-tools focus, via manual web research — NOT via APE's Research engine, since APE's source coverage doesn't yet cover this reliably either, though it's the closest-fit category to APE's existing HN/GitHub sources).
- First-pass elimination (15→5): kept #5 (Semantic LLM Cache), #6 (Energy/Sleep Diagnostics), #8 (Uptime/SSL Monitor), #9 (AI Database Seeder), #10 (CI/CD YAML Debugger).
- **Competitive/prior-art check results (critical — checked live via web search before committing dev time):**
  - #9 AI Database Seeder: direct competitor **Snaplet** (YC-backed) built the same idea, shut down mid-2026, now stale open-source fork. Real gap exists but requires a clearly demonstrated "why not the free fork" answer.
  - #5 Semantic LLM Cache: crowded, active, well-funded competitors (GPTCache, Cloudflare AI Gateway, Upstash, Helicone). Documented real-world failure mode (cross-customer cache data leak). High risk for a 7-day solo MVP.
  - #10 CI/CD YAML Debugger: **GitHub itself shipped "Agentic Workflows"** (native AI CI-failure analysis in Copilot, Feb 2026) — platform-level existential threat.
  - #6 Energy/Sleep Diagnostics: direct, live, well-featured competitor **LidRun** already targets the exact AI-developer niche.
  - #8 Uptime/SSL Monitor: not yet checked.
- **Decision pending:** none of the 5 candidates is risk-free; #9 currently the least-bad option but needs a sharper differentiation story. #8 competitive check still outstanding.

## Next Objective

Pick 1 candidate → ship MVP in ≤14 days (7 preferred) → get 1 real user → get 1 real payment. Research is closed once a candidate is picked; no further "let's validate more" cycles without a hard blocker.

## Resume Instructions

1. Read this file first.
2. Read `docs/roadmap.md` (being corrected alongside this file — do not trust its Sprint 6.x history as current).
3. Do not restart or re-relitigate RA-020/021/022 or the ORION-155 finding — they are closed/settled.
4. Do not propose new governance/architecture/Council systems without first checking this file's "Current Phase" section.
5. If resuming opportunity selection: continue from "Opportunity Discovery Status" above — check #8, then finalize 5→3→1.