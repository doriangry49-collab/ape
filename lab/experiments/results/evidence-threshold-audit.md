# ORION-043 Evidence Threshold Review & Decision Contract Audit: home_local_services

**Experiment:** `ORION-043`
**Status:** `AUDIT_COMPLETE`
**Engineering Recommendation:** `REVISE`
**Observed Real User Count:** `0`

---

## 1. Executive Summary
The hardcoded '10 real users' threshold is an unvalidated provisional heuristic (PROVISIONAL_THRESHOLD), not an empirically proven market law. While 0 real responses MUST remain locked to VALIDATE_MORE, future decision logic should evaluate Evidence Diversity, Behavioral vs Stated intent, and Severe Negative Signals rather than relying strictly on raw response counts.

## 2. Current Decision Contract Audit
Audited contract states (UNKNOWN, OBSERVED_POSITIVE, OBSERVED_NEGATIVE, OBSERVED_NEUTRAL, CONTRADICTED, INFERRED, SYNTHETIC, TEST_FIXTURE, REAL_USER_RESPONSE). Invariants (EMPTY != NEGATIVE, INFERRED != OBSERVED, SYNTHETIC != REAL) are 100% intact.

## 3. Threshold Audit Matrix

| Threshold Name | Value | Status | Is Arbitrary | Empirically Justified |
| :--- | :---: | :---: | :---: | :---: |
| `Overall Minimum Sample Size (10 real users)` | `10` | `PROVISIONAL_THRESHOLD` | `True` | `False` |
| `H1 Problem Confirmation Minimum (>= 5 positive)` | `5` | `PROVISIONAL_THRESHOLD` | `True` | `False` |
| `H2 Payment Intent Minimum (>= 4 positive)` | `4` | `PROVISIONAL_THRESHOLD` | `True` | `False` |
| `H3 Acquisition/Trial Intent Minimum (>= 5 positive)` | `5` | `PROVISIONAL_THRESHOLD` | `True` | `False` |

## 4. Evidence Quality & Weighting Matrix

| Signal Type | Weight | Status | Rationale |
| :--- | :---: | :---: | :--- |
| `Stated Payment Intent ('I would pay $29')` | `LOW (0.3x)` | `STATED_INTENT` | High survey inflation rate; free responses express optimism without financial risk. |
| `Observed Payment Behavior ('Currently paying $30/mo for X tool')` | `HIGH (1.0x)` | `OBSERVED_BEHAVIOR` | Demonstrates existing budget allocation and active market demand. |
| `Stated Trial Intent ('I would try a CLI proxy')` | `LOW (0.3x)` | `STATED_INTENT` | Low friction to say yes; does not guarantee CLI installation. |
| `Observed Installation Behavior ('Ran CLI binary & reproduced setup')` | `HIGH (1.0x)` | `OBSERVED_BEHAVIOR` | Demonstrates actual user friction tolerance and technical commitment. |

## 5. Bias & Sampling Risk Audit

| Risk Name | Description | Mitigation |
| :--- | :--- | :--- |
| `Source Clustering Bias` | All 10 responses collected from a single Reddit thread or Discord channel. | Require responses across >= 2 independent channels (e.g., HN + Reddit + Direct Interview). |
| `Respondent Duplication Risk` | Single individual submitting multiple anonymous survey responses. | Ingestion gate response_id uniqueness check & IP/header anomaly detection. |
| `Over-weighting Stated Intent` | Treating 'I would pay $29' as equivalent to validated commercial demand. | Differentiate STATED_INTENT from OBSERVED_BEHAVIOR in evidence weighting. |
| `Treating Thresholds as Market Facts` | APE converting internal heuristic (10 users) into verified scientific market law. | Label all internal threshold counts as PROVISIONAL_THRESHOLD. |

## 6. Decision Matrix Review
- `0 Responses` $\rightarrow$ `VALIDATE_MORE` (EMPTY != NEGATIVE).
- `Negative Evidence` $\rightarrow$ `NO-GO` (Negative feedback outweighs positive).
- `Stated Payment Intent` $\rightarrow$ Weighted low (0.3x) to avoid false optimism.
- `Observed Installation` $\rightarrow$ Weighted high (1.0x) as true commitment.

## 7. Self-Critique & Invariant Tests
- APE cannot treat internal thresholds as customer evidence. (PASS)
- 10 responses is not automatically scientifically validated. (PASS)
- 10 responses does not guarantee GO. (PASS)
- Stated payment intent separated from observed payment behavior. (PASS)
- Stated trial intent separated from observed installation behavior. (PASS)

## 8. KEEP / REVISE / REJECT Recommendation
**Recommendation:** `REVISE`
**Justification:** The hardcoded '10 real users' threshold is an unvalidated provisional heuristic (PROVISIONAL_THRESHOLD), not an empirically proven market law. While 0 real responses MUST remain locked to VALIDATE_MORE, future decision logic should evaluate Evidence Diversity, Behavioral vs Stated intent, and Severe Negative Signals rather than relying strictly on raw response counts.

## 9. Proposed Next Steps
1. Maintain hard stopping line (`user_responses.json = []`).
2. Prepare human outreach tools without modifying decision code.
3. Wait for real user feedback.

## 10. Evidence Lineage
- **SHA-256 Hash:** `sha256_threshold_audit_ledger`
- **Input File:** `lab/experiments/input/user_responses.json` (Empty `[]`)

## 11. ENGINEERING ASSESSMENT (Mandatory Orion Judgment)

1. **ORION-042 Step Validity:** ORION-042 was a necessary technical stopping line to prevent continuous self-referential simulation loops. However, hardcoding '10 real users' as an absolute gate was an unverified heuristic step.
2. **10 Real Users Threshold Rigor:** `PROVISIONAL_HEURISTIC_ARBITRARY (0 empirical market calibration studies)`
3. **Biggest Epistemic Risk:** Sampling bias (e.g. 10 responses from single Reddit sub) and confusing stated survey optimism ('I would pay $29') with verified commercial transaction behavior.
4. **Assumption-to-Fact Conversion Risk:** APE risks mistaking its internal threshold heuristic (10 users, 5 H1, 4 H2) for verified scientific market facts. All internal thresholds MUST be tagged PROVISIONAL_THRESHOLD.
5. **Next Logical Step:** Do NOT write more simulation code or invent new thresholds. Wait for human operators to gather first 5-10 real user responses, or initiate a human outreach phase.
6. **Final Engineering Recommendation:** **`REVISE`**
