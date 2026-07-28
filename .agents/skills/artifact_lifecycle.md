# Skill: Artifact Lifecycle & Pointer Model

APE structures its outputs into a clean model separating execution state from history.

## 1. Directory Structure Rules
- **Canonical Current State (`.build/`):**
  - Path format: `.build/<track>/<slug>.json`
  - Mutable. Overwritten on each run.
  - Excluded from git.
  - Used for fast, O(1) reads by downstream modules.
- **Immutable History (`.governance/`):**
  - Path format: `.governance/evidence/<track>.jsonl`
  - Append-only. Never modified or truncated.
  - Serves as the audit trail of APE actions.

## 2. Utility API Usage
Use the helper functions defined in `src/ape/utils.py`:
- `get_current_artifact(build_dir, slug)` -> Retrieves canonical pointer.
- `append_to_evidence(evidence_dir, track, payload)` -> Appends to history log.
- `make_artifact_id()` -> Generates time-sortable collision-safe IDs.
