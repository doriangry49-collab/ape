# Roadmap

## Sprint 1
- Completed: establish a minimal Python package structure.
- Completed: provide a simple `ape doctor` command for environment inspection.
- Completed: introduce basic test coverage and project metadata.

## Sprint 3
- Completed: add configuration foundation support.
- Completed: implement `ape config` for workspace inspection.
- Completed: add regression tests for configuration behavior.

## Sprint 4 — Workspace Discovery (Completed)
- Completed: detect an APE workspace from child directories.
- Completed: search parent directories for `.ape/config.toml`.
- Completed: keep existing commands unchanged.
- Completed: add regression tests.
- Completed: keep dependencies unchanged.

## Sprint 5 — Project Model (Completed)
- Completed: define a lightweight Project abstraction for future CLI use.
- Completed: introduce reusable project loading.
- Completed: add Project configuration support and built-in TOML parsing via `tomllib`.
- Completed: expose `Project.config` and read-only Project properties.
- Completed: add regression tests and keep dependencies unchanged.

## Sprint 6.1 — Project Services (Completed)
- Completed: add `Project.name` as a lightweight project service.
- Completed: add `Project.metadata` to expose reusable project information.
- Completed: keep the Project API read-only and backward compatible.
- Completed: preserve CLI behavior and add regression coverage.
- Completed: keep dependencies lean and maintainable.

## Sprint 6.2 — Project Services (Planned)
- Expand reusable project information services for the future service layer.
- Keep existing CLI commands backward compatible.
- Preserve regression coverage and CLI behavior.
- Keep dependencies lean and maintainable.

## Near-Term Priorities
- Expand CLI commands only when there is a clear user need.
- Keep dependencies lean and maintainable.
- Document architectural decisions as the project grows.

## Post-Sprint-6.2 — Actual Development (RA Remediation Track)

> Not: Bu bölüm eklenene kadar roadmap.md, RA-020/021/022 döngüsünü ve 
> governance/research/decision/execution altyapısının gerçek gelişimini 
> hiç yansıtmıyordu. Detaylar için PROJECT_CONTEXT.md'ye bakın.

- RA-020 (Completed): Docker/WSL2 sandbox mount path fix.
- RA-021 (Completed): Forensic finding — tasks were marked COMPLETED via 
  exploratory search/read_file alone, with no real artifact produced.
- RA-022 (Completed): DeliverableVerifier alternative-path parsing fix; 
  task completion semantics now require a real write action.
- ReportAssembler / BriefGenerator (Completed, live-execution verified): 
  `ape brief <slug>` command, deterministic EXECUTIVE_BRIEF.md generation.
- ORION-155 claim (Debunked): forensically confirmed to be mock/dry-run 
  only, not real production proof. Do not cite as evidence of anything.
- Current phase: Product-first pivot — opportunity discovery for a 
  shippable niche MVP (≤14 days). See PROJECT_CONTEXT.md for live status.
