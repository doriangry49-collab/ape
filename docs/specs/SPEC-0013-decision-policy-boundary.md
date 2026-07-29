# SPEC-0013: RFC-013 Decision / Policy Boundary Contract

**Status:** APPROVED & FORMALIZED  
**Author:** Antigravity (Implementation Engineer) & Lead Architect  
**Sealed:** 2026-07-29  

## 1. Overview

This specification establishes the formal, deterministic boundary separating Business Policy Decisions from Task Execution in APE. It defines the canonical `PolicyDecision` model, the contract for `ConstitutionValidator.evaluate_policy()`, the lineage propagation requirements from `InferenceBridge` to `DecisionReport`, and the strict Policy $\rightarrow$ Execution boundary enforced at `RoadmapGenerator`.

## 2. Core Invariants

1. **Strict Business Policy Enumeration**: All business decisions MUST be instances of `PolicyDecision` (`BUILD`, `VALIDATE`, `WATCH`, `IGNORE`, `BLOCKED`). String literals for policy decisions are deprecated.
2. **`UNKNOWN` Fail-Closed Protection**: If any critical evidence flag (`payment_signal`, `identifiable_customer`, `ai_solvability`) evaluated by `InferenceBridge` is `UNKNOWN`, `False`, or `None`, `PolicyDecision.BUILD` is **strictly forbidden**.
3. **Determinism**: Given identical score inputs and evidence flag inputs, `ConstitutionValidator.evaluate_policy()` MUST always return the exact same `PolicyGateResult`.
4. **Complete Audit Lineage**: Derived `DecisionReport` objects MUST preserve `provenance_chain` (list of `EvidenceProvenance`), `reference_urls`, `evidence_flags`, `evidence_hash`, and rule ID rationale.
5. **Policy Gate / Execution Isolation**: Policy Gate (`DecisionEngine`) performs zero task execution; Execution Engine (`ExecutionEngine`) performs zero business policy evaluation.

## 3. Policy Decision Enumeration

| PolicyDecision | Description | Downstream Action Allowed |
| :--- | :--- | :--- |
| **`BUILD`** | High score & verified positive evidence. | RoadmapGenerator emits MVP development roadmap. |
| **`VALIDATE`** | Borderline score OR high score missing evidence. | RoadmapGenerator emits market validation roadmap (landing page/surveys). |
| **`WATCH`** | Moderate score or unverified signal. | Roadmap generation blocked; monitor market signals. |
| **`IGNORE`** | Low score OR catastrophically low feasibility (<20). | Roadmap generation blocked; discard opportunity. |
| **`BLOCKED`** | Hard constitutional gate or security policy stop. | Roadmap generation blocked; flag governance alert. |

## 4. Policy Gate Decision Matrix

Inputs: `overall_score`, `vector_scores`, `BridgeResult` (`evidence_flags`).

```text
                  feasibility < 20?
                     /        \
                  YES          NO
                  /              \
            [IGNORE]        Critical Flags All True?
                               /        \
                            YES          NO (or UNKNOWN)
                            /              \
                overall_score >= 60?    overall_score >= 60?
                    /        \             /        \
                 YES          NO        YES          NO
                 /              \       /              \
             [BUILD]        score >= 40? [VALIDATE]  score >= 40?
                               /      \                 /      \
                           [VALIDATE] [WATCH]       [WATCH]  [IGNORE]
```

## 5. Lineage & Provenance Invariants

- `DecisionReport` serialized JSON (`.build/decisions/<slug>.json`) and JSONL log (`.governance/evidence/decisions.jsonl`) MUST contain:
  - `provenance_chain`: list of `EvidenceProvenance` items from input `BridgeResult`.
  - `reference_urls`: list of unique supporting URLs.
  - `evidence_flags`: dictionary snapshot of inferred signal flags.
  - `decision`: string representation of `PolicyDecision`.
  - `rule_id`: unique identifier of the constitutional rule applied.

## 6. Execution Boundary

- `RoadmapGenerator.generate_roadmap()` MUST verify the `PolicyDecision` of the decision artifact:
  - Allowed: `BUILD`, `VALIDATE`
  - Blocked: `WATCH`, `IGNORE`, `BLOCKED` (Raises `ValueError` / `PolicyExecutionBlockedError`).
