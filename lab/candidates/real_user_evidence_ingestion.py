from __future__ import annotations

from typing import Any, Dict, List, Tuple


class RealUserEvidenceIngestionValidator:
    """
    R&D Ingestion Gate for Real User Evidence.
    Validates user response JSON payloads before passing them to evaluation engines.
    Strictly rejects synthetic data, missing response_ids, duplicate IDs, empty entries, and PII.
    Converts missing optional survey fields to UNKNOWN without rejecting the payload.
    """

    FORBIDDEN_PII_FIELDS = {"name", "email", "phone", "address", "ip", "location"}
    VALID_SOURCES = {"reddit", "hackernews", "direct_interview", "survey", "landing_page", "other"}

    def validate_responses(self, raw_responses: List[dict[str, Any]]) -> Tuple[List[dict[str, Any]], List[str]]:
        """
        Validates raw response entries. Returns (clean_valid_responses, rejection_errors).
        """
        clean_responses: List[dict[str, Any]] = []
        errors: List[str] = []
        seen_ids: set[str] = set()

        for idx, entry in enumerate(raw_responses, 1):
            # Rule 1: Synthetic data rejection
            if entry.get("is_synthetic", False):
                errors.append(f"Entry {idx}: Rejected synthetic data payload (is_synthetic=True).")
                continue

            # Rule 2: Missing required response_id
            resp_id = entry.get("response_id")
            if not resp_id or not str(resp_id).strip():
                errors.append(f"Entry {idx}: Rejected missing or empty required field 'response_id'.")
                continue

            resp_id_str = str(resp_id).strip()

            # Rule 3: Duplicate response_id rejection
            if resp_id_str in seen_ids:
                errors.append(f"Entry {idx}: Rejected duplicate response_id '{resp_id_str}'.")
                continue
            seen_ids.add(resp_id_str)

            # Rule 4: PII Protection
            pii_found = [k for k in entry.keys() if k.lower() in self.FORBIDDEN_PII_FIELDS]
            if pii_found:
                errors.append(f"Entry '{resp_id_str}': Rejected presence of forbidden PII fields ({', '.join(pii_found)}).")
                continue

            # Rule 5: Completely blank response entry rejection
            has_content = any([
                entry.get("free_text"),
                entry.get("problem_frequency"),
                entry.get("trial_interest") is not None,
                entry.get("payment_interest") is not None,
                entry.get("current_spend"),
            ])
            if not has_content:
                errors.append(f"Entry '{resp_id_str}': Rejected completely blank response record.")
                continue

            # Normalize source
            source = str(entry.get("source", "")).lower().strip()
            normalized_source = source if source in self.VALID_SOURCES else "UNKNOWN"

            # Clean response entry
            clean_entry = {
                "response_id": resp_id_str,
                "source": normalized_source,
                "target_customer_match": entry.get("target_customer_match", False),
                "problem_frequency": entry.get("problem_frequency"),  # None if missing -> UNKNOWN
                "trial_interest": entry.get("trial_interest"),        # None if missing -> UNKNOWN
                "payment_interest": entry.get("payment_interest"),    # None if missing -> UNKNOWN
                "current_spend": entry.get("current_spend"),
                "free_text": str(entry.get("free_text", "")).strip(),
                "is_synthetic": False,
            }
            clean_responses.append(clean_entry)

        return clean_responses, errors
