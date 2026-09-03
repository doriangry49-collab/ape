# APE – Next Session

## Read Order

1. `PROJECT_CONTEXT.md` (just corrected — this is now the real, verified state)
2. This file
3. `docs/roadmap.md` (being corrected alongside — historical Sprint 1–6.2 entries are legacy scaffolding history, not current)

## Current Phase

Post-RA-022. Product-first pivot in effect ("USE THE MACHINE"). See PROJECT_CONTEXT.md "Current Phase" section for full rules.

## Immediate Next Actions (in order)

1. **Close the ReportAssembler verification loop:** run
   ```
   git status --short -- deliverables/gebze_kocaeli_emlak_ai_sanal_staging/EXECUTIVE_BRIEF.md
   Get-FileHash deliverables\gebze_kocaeli_emlak_ai_sanal_staging\EXECUTIVE_BRIEF.md -Algorithm SHA256
   ```
   to confirm whether the file is git-tracked, and get a direct content hash (not git-diff-based) determinism proof. Once done, ReportAssembler is fully sealed — no further work on it without a new demonstrated blocker.
2. **Finish the competitive check on candidate #8** (Minimalist Uptime/SSL Monitor) — same method as #5/#6/#9/#10 (live web search for "already tried / already exists / shut down").
3. **Finalize 5→3 selection** among the opportunity candidates using the competitive findings already gathered. Do not reopen #1–#4, #7, #11–#15 (already eliminated with reasons in PROJECT_CONTEXT.md history / prior session transcripts) unless a new blocker specifically requires it.
4. **Pick 1 candidate.** Once picked, research stops. No further validation cycles.
5. **Ship MVP.** Target ≤14 days, 7 preferred. No new architecture, no Docker/governance changes unless the MVP itself hits a real blocker.

## Development Rules (in effect now)

- No new RFC, governance document, Council/dashboard system, or R&D promotion without a demonstrated real-workload blocker.
- Every "COMPLETED" or "PASS" claim must be backed by live command output (mtime, git status, real pytest run, real CLI stdout) — not code-reading alone, not summarized test counts.
- Update this file and `PROJECT_CONTEXT.md` after every RA-round or every completed real-workload run. This rule was previously written but not followed — do not repeat that failure.
- Antigravity: continue using the Context Intelligence Protocol (`.agents/skills/context-intelligence/SKILL.md`) for minimal-context retrieval — that part of the workflow is working well and should not change.