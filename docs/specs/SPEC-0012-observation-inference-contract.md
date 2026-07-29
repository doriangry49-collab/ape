# SPEC-0012: RFC-012 Observation → Inference Contract

**Status:** APPROVED & FORMALIZED  
**Author:** Antigravity (Implementation Engineer) & Lead Architect  
**Sealed:** 2026-07-29  

## 1. Overview

This specification establishes the formal, deterministic contract for converting raw business observations (`BusinessEvidence`) into high-level business inference flags (`payment_signal`, `identifiable_customer`, `ai_solvability`) consumed by the `ConstitutionValidator`.

## 2. Core Invariants

1. **`UNKNOWN != FALSE`**: `UNKNOWN` represents an indeterminate observation (absence of signal in a given source result). It is NOT boolean `False`.
2. **`UNKNOWN != TRUE`**: `UNKNOWN` can never be promoted to boolean `True` without positive evidence.
3. **`ERROR != UNKNOWN`**: Provider, network (`4xx`/`5xx`), or parsing errors raise `AdapterError` and produce **zero evidence** (`NO EVIDENCE`). They must never be converted to `UNKNOWN`.
4. **`NO EVIDENCE != POSITIVE EVIDENCE`**: Empty evidence sets map all inference flags to `UNKNOWN`, which safely blocks `BUILD` policy in `ConstitutionValidator`.
5. **Observation Isolation**: Adapters strictly emit raw observations (`pricing_observation`, `manual_work_observation`, etc.). They MUST NOT set inference flags directly.

## 3. Aggregation Truth Table

When combining observations across multiple `BusinessEvidence` objects:

| Observation A | Observation B | Aggregate Result | Justification & Policy |
| :--- | :--- | :--- | :--- |
| **TRUE** | **TRUE** | **TRUE** | Dual positive evidence confirms signal. |
| **TRUE** | **UNKNOWN** | **TRUE** | Positive observation prevails when other source is indeterminate. |
| **FALSE** | **FALSE** | **FALSE** | Dual negative evidence confirms absence of signal. |
| **FALSE** | **UNKNOWN** | **FALSE** | Explicit negative observation prevails over indeterminate. |
| **TRUE** | **FALSE** | **UNKNOWN** | **Conflict Policy:** Contradictory evidence triggers indeterminate `UNKNOWN`, forcing user validation. |
| **UNKNOWN** | **UNKNOWN** | **UNKNOWN** | Neither source established an observation. |
| **NO EVIDENCE** | - | **UNKNOWN** | Zero evidence produces `UNKNOWN`. |

## 4. Observation to Inference Mapping

| Inference Flag | Source Observations | Derivation Rule |
| :--- | :--- | :--- |
| **`payment_signal`** | `pricing_observation`, `competition_observation` | `True` if `pricing == TRUE` OR `competition == TRUE`<br>`False` if `pricing == FALSE` AND `competition == FALSE`<br>Else `UNKNOWN` |
| **`identifiable_customer`** | `search_intent_observation`, `entity_observation` | `True` if `search_intent == TRUE` OR `entity == TRUE`<br>`False` if `search_intent == FALSE` AND `entity == FALSE`<br>Else `UNKNOWN` |
| **`ai_solvability`** | `manual_work_observation` | `True` if `manual_work == TRUE`<br>`False` if `manual_work == FALSE`<br>Else `UNKNOWN` |

## 5. Provenance & Lineage Invariants

- Derived `BridgeResult` objects MUST preserve the complete `provenance_chain` (list of `EvidenceProvenance` objects from all contributing `BusinessEvidence` items).
- All valid `reference_url` values from contributing evidence MUST be collected and preserved in `BridgeResult.reference_urls`.

## 6. Constitution Integration

The output `evidence_flags` dictionary maps directly to `ConstitutionValidator.evaluate_business_gate(overall_score, evidence_flags)`.
- If any required flag is `UNKNOWN`, `False`, or `None`, `evaluate_business_gate()` evaluates `is not True`, blocking the `BUILD` (GO) decision and routing the policy to `VALIDATE`, `WATCH`, or `IGNORE`.
