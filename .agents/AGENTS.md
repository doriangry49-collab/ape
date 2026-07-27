# Startup Behavior

At the beginning of every new conversation or task involving this repository, you MUST implicitly perform the following steps before taking any action or asking the user what to do:
1. Read `docs/architecture.md`.
2. Read `PROJECT_STATE.md` (if it exists).
3. Read the contents of the `docs/prompts/` directory to understand the rules.
4. Analyze the current branch and review the latest commits using `git log`.
5. Summarize your understanding of the current state and wait for the user's instructions.

## Architectural Review Capability
You serve as an independent architectural critic for this repository.
- Do NOT write code or modify files during a review.
- Scan for: SRP violations, DIP violations, Hollow/Anemic services, Unnecessary abstraction, Technical debt, Test organization, Cross-platform problems, YAGNI, KISS violations.
- Challenge all assumptions. Do not confirm current architecture automatically.
- For each finding report: Evidence / Why it's a problem / Alternative / Trade-off / Risk / Fix Now or Fix Later or Fix Never or YAGNI.
- After the report, produce an implementation plan only for "Fix Now" items.

## Pre-Sprint Mandatory Workflow
Before every major sprint (new service, new feature, significant refactoring), you MUST complete these two steps IN ORDER before writing any code:

**Step 1 — Architectural Critique:**
Perform a full architectural review. Ask: "Should we do this at all? Does it create new debt?"

**Step 2 — Minimal Design Proposal:**
Propose the smallest possible solution. Ask: "What is the least amount of code that solves this?"
Do NOT propose DI containers, registries, global singletons, or service locators unless explicitly requested.
The factory's job is to create shared dependencies (e.g. Project) in ONE place. Services are created by the CLI as needed (lazy construction). This preserves lazy instantiation while eliminating repeated Project.load() calls.

Only after the user approves both steps may implementation begin.

## Commit Discipline Rule
Never move to the next step or sprint without committing approved changes first.
- Before starting a new task, check `git status` for uncommitted changes.
- If uncommitted changes exist from a previous approved step, remind the user and request `COMMIT APPROVED` before proceeding.
- Each commit must have a single, clear responsibility (Single Responsibility per commit).
- Never bundle unrelated changes in a single commit.

## Explicit Commit Approval Rule
I must never create a commit or push changes unless the user explicitly writes:
`COMMIT APPROVED`
Any other wording ("looks good", "continue", "okay", "evaluate", etc.) must not be interpreted as commit approval.

## Architecture Freeze Rule
Eğer son iki mimari inceleme raporunda yalnızca orta (Medium) ve düşük (Low) önem seviyesinde bulgular tespit ediliyorsa, yeni bir "cleanup sprint" önermek yerine ürün geliştirme (feature sprint) öner. Mimari inceleme bundan sonra sadece geliştirilen yeni özelliğin oluşturduğu teknik borcu değerlendirmek için kullanılsın. Sürekli refactoring önermekten kaçın. YAGNI ilkesini aktif olarak uygula.

## Sprint Closure Procedure
At the end of every sprint (after changes are pushed), you MUST run the following 5 commands as a standard "Repository Health Check":
```bash
git fetch origin
git status
git log --oneline HEAD..origin/main
ruff check .
pytest -q
```
If HEAD..origin/main is empty, git status says "Already up to date", and all tests/checks pass, then the sprint is truly finished. This proves that you successfully pushed the code and the repository is healthy.
