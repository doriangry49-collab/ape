# APE — Autonomous Product Engine

APE (Autonomous Product Engine) is a governed autonomous build framework designed to transition software projects safely through research, constitutionally bounded decision-making, intelligent planning, sandbox-isolated agent execution, and human-approved release gates.

---

## 🏛️ Governed Autonomous Build Architecture

The entire lifecycle is orchestrated under strict constitutional policy invariants (RFC-014 through RFC-019):

```text
USER CLI: ape build "<topic>" [--yes]
  │
  ├─▶ Step 0/4: Research Signal Check (ResearchEngine -> .build/research/<slug>.json)
  ├─▶ Step 1/4: Decision Gate (ConstitutionValidator -> BUILD/VALIDATE policy enforcement)
  ├─▶ Step 2/4: Execution Roadmap (RoadmapGenerator -> Canonical action whitelist filtering)
  ├─▶ Step 3/4: Governed Execution Engine (ExecutionEngine -> ApeCoderAgent -> Sandbox -> Bounded Repair Loop)
  └─▶ Step 4/4: Governed Release Gate (ReleaseGate -> Quality Pre-check -> Human Approval -> Lineage Git Commit)
```

---

## 🚀 CLI Commands

### End-to-End Autonomous Build
- **`ape build "<topic>" [--yes]`**: Executes the complete 4-stage governed autonomous build journey for a natural-language topic or task. Halts automatically at Step 1 if the decision is not `BUILD` or `VALIDATE`.

### Stage-by-Stage CLI Subcommands
- **`ape scan [--mode tech|business]`**: Scans GitHub Trending and Hacker News for daily tech opportunities or business signals.
- **`ape research "<topic>"`**: Conducts market, competitor, and pain-point research for a given topic.
- **`ape decide "<topic>"`**: Evaluates research data against constitutional scoring rules to produce a formal `BUILD`, `VALIDATE`, `WATCH`, or `IGNORE` policy decision.
- **`ape plan "<topic>"`**: Generates a milestone execution roadmap with canonical action constraints.
- **`ape execute "<topic>" [--no-dry-run]`**: Runs the execution engine over the generated roadmap.
- **`ape release "<topic>" [--yes]`**: Evaluates syntax quality checks and creates a lineage-embedded git commit upon human approval.
- **`ape validate`**: Runs system-wide governance integrity and test suite validation.
- **`ape doctor`**: Displays workspace and environment health diagnostics.

---

## 🛡️ Governance & Security Guarantees

1. **No Automatic `git push`**: Remote pushing is FORBIDDEN and blocked by policy. Releases create local commits with human approval.
2. **Fail-Closed Container Sandbox**: Isolated execution runs inside Docker sandboxes with `--network=none`, CPU/memory quotas, and zero host environment propagation. If Docker is unavailable, live execution fails closed (`BLOCKED`).
3. **Audit Lineage**: All events log immutable, append-only audit evidence under `.governance/evidence/<track>-YYYY-MM.jsonl` with embedded `decision_id`, `policy_decision`, and `evidence_hash` lineage.

---

## 🔒 Secret Scanning

This repository uses [gitleaks](https://github.com/gitleaks/gitleaks) for local pre-commit secret scanning and CI workflow protection.

To enable local secret scanning before committing:
```bash
pip install pre-commit
pre-commit install
```

---

## 📋 Project Status & Tracking

Live project status, sprint backlog, and mission tracking are managed via [GitHub Issues](https://github.com/doriangry49-collab/ape/issues).

