# Skill: Execution Safety Policy

Execution in APE is governed by strict boundaries to prevent unintended system changes.

## 1. Mappings
Actions must be classified prior to run via `ExecutionPolicy.classify(action)`:
- **`SAFE`:** Auto-run (e.g. read file, run tests, create new files).
- **`REQUIRES_APPROVAL`:** CLI prompt and pause (e.g. modify existing source code/configs, git commit/push, delete, deploy, external API write).
- **`FORBIDDEN`:** Instantly fail execution (e.g. credential exposure, financial action).

## 2. Dry-Run Default Rules
- Execution default state is `SimulationTaskExecutor`.
- Dry-run modes must mock operations and must not write mutations to git or project code.
- Verification checks that deliverables exist, but in dry-run mode, verification is auto-passed.
