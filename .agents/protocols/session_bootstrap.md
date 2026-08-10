# Protocol: Session Bootstrap

At the beginning of every new session, conversation, or task, the operating agent MUST execute the following bootstrap pipeline to establish absolute context:

## 1. Bootstrap Pipeline Order

0. **Repository Identity Verification (FAIL-CLOSED PREREQUISITE):**
   Before inspecting source code, loading state, or executing tasks, verify the operating repository identity:
   ```bash
   git rev-parse --show-toplevel
   git remote -v
   git branch --show-current
   git rev-parse HEAD
   ```
   If root, remote, branch, or HEAD mismatch canonical project expectations, trigger **`REPOSITORY IDENTITY MISMATCH — STOP`** immediately. Do NOT modify files, execute tests, generate state, or commit.

1. **Read `START_HERE_AI.md`:** Look for any high-level instructions written specifically for new AI entries.
2. **Read `.agents/AGENTS.md`:** Read the entry point of the APE AI Collaboration Layer.
3. **Load Active Role Rules:** Read the roles (`lead_architect.md` or `systems_engineer.md`) relative to your current agent scope.
4. **Compile Context:** Run `python src/ape/cli.py context --all`.
5. **Inspect Current State:** Read `.build/` to locate the current active roadmaps, execution state, and decisions.
6. **Audit Governance Evidence:** Inspect `.governance/evidence/` logs to trace recent run events.
7. **Load Latest Handoff:** Read the latest Handoff Report from chat history or previous walkthroughs.


---

## 2. Next Milestones (NEXT)
> [!NOTE]
> **Tracked Handoff State:**
> Currently, the Handoff Protocol relies on chat history or manual walkthrough logs.
> A future sprint will introduce a tracked, persistent state file (e.g. `.build/execution/handoff.json` or `.agents/handoff_state.json`) to completely automate session-to-session continuity in version control.
