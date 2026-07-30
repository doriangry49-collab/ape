# APE R&D Lab (`lab/`) Boundary & Experimentation Guidelines

**Status:** ACTIVE R&D SANDBOX  
**Governance:** Governed by `SPEC-0017` Import Boundary and Promotion Gate Protocols  

---

## 1. Purpose

The `lab/` directory is an isolated sandbox for experimental candidate algorithms, new data source adapters, candidate models, and performance benchmarks. It allows rapid prototyping without risking production stability or polluting production test suites.

---

## 2. Directory Structure

```text
lab/
├── README.md               # This document
├── experiments/            # Active candidate experiments (e.g. exp_001_scoring.py)
├── candidates/             # Candidate implementations awaiting promotion validation
│   ├── scanners/           # Experimental scanners
│   ├── models/             # Experimental data models & prompts
│   └── adapters/           # Experimental search/API adapters
├── benchmarks/             # Performance, precision & memory benchmark scripts
└── fixtures/               # Isolated R&D test fixtures (zero pollution of tests/)
```

---

## 3. Import Isolation Invariants

1. **`production -> lab` (FORBIDDEN / YASAK):** No module under `src/ape/` may import any file, class, or symbol from `lab/`. Verified deterministically by `scripts/check_import_boundaries.py`.
2. **`lab -> production` (READ-ONLY ALLOWED):** Experimental modules under `lab/` MAY import public interfaces, models (`Opportunity`, `TaskStatus`), and utilities from `ape` (`from ape.intelligence.models import Opportunity`). Experimental code MUST NOT mutate or monkey-patch production classes.
3. **`lab -> tests` (FORBIDDEN):** Experimental code under `lab/` MUST NOT import from `tests/`.

---

## 4. Execution & Testing

* **Run Experiments:** `python -m lab.experiments.exp_001`
* **Run Lab Tests:** `uv run pytest lab/`
* **Production CI:** `uv run pytest -m "not integration"` (executes `tests/` only, completely bypassing `lab/`).

---

## 5. Promotion Gate (Lab -> Production)

Before candidate code under `lab/candidates/` can be promoted into production `src/ape/`, it MUST satisfy all 8 mandatory promotion gates:

1. **Functional Experimentation (S-1):** Successful evaluation script in `lab/candidates/`.
2. **Reproducibility (S-2):** 3 consecutive deterministic test runs.
3. **Evidence Audit (S-3):** Verified `SPEC-0012` compliance (`ERROR != UNKNOWN`, zero synthetic mock evidence on failure).
4. **Unit Tests (S-4):** 100% test coverage implemented under `tests/`.
5. **Benchmark (S-5):** Performance and memory metrics $\le$ baseline.
6. **Contract Audit (S-6):** Compliance sign-off with sealed contracts (`SPEC-0012..016`, `RFC-021`).
7. **Human Approval (S-7):** Explicit authorization from Human Operator.
8. **Manual Promotion (S-8):** Manual file move from `lab/candidates/` to `src/ape/` with git commit. *(Automated promotions forbidden).*
