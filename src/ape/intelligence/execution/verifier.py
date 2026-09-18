"""
Deliverable Verifier — deterministic, no network, no LLM.

MVP rule: a task is VERIFIED if all declared deliverable file paths exist on disk,
are non-zero in size, and (if .json) contain valid JSON.

In dry-run mode, verification is skipped (nothing was created).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Union


class DeliverableVerificationResult:
    """
    Result of deliverable verification.

    Iterable/unpackable as (passed, missing_items) for backward compatibility,
    with .passed (bool), .missing_items (list[str]), and .reasons (dict[str, str])
    attributes mapping failed deliverable -> failure reason.
    """

    def __init__(
        self,
        passed: bool,
        missing_items: list[str],
        reasons: dict[str, str] | None = None,
    ) -> None:
        self.passed: bool = passed
        self.missing_items: list[str] = missing_items
        self.reasons: dict[str, str] = reasons if reasons is not None else {}

    def __iter__(self):
        yield self.passed
        yield self.missing_items

    def __getitem__(self, index):
        return (self.passed, self.missing_items)[index]


class DeliverableVerifier:
    def __init__(self, project_root: Optional[Path] = None, dry_run: bool = False) -> None:
        self._root = project_root if project_root is not None else Path(".")
        self._dry_run = dry_run

    @staticmethod
    def _parse_deliverable_item(item: str) -> list[str]:
        """
        Parses a deliverable description string into candidate file paths.
        Supports:
        - Alternatives via ' or ' (e.g., 'package.json or pyproject.toml' -> ['package.json', 'pyproject.toml'])
        - Descriptive suffixes (e.g., 'README.md file' -> ['README.md'])
        """
        cleaned = item.strip()
        for suffix in (" file", " module", " script", " entry point script"):
            if cleaned.lower().endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()

        if " or " in cleaned:
            parts = [p.strip() for p in cleaned.split(" or ")]
            candidates = []
            for p in parts:
                for suffix in (" file", " module", " script", " entry point script"):
                    if p.lower().endswith(suffix):
                        p = p[:-len(suffix)].strip()
                if p:
                    candidates.append(p)
            return candidates

        return [cleaned] if cleaned else []

    @staticmethod
    def _validate_file(path: Path) -> str | None:
        """
        Validates a candidate file path.

        Returns None if valid, or a failure reason string:
        - "NOT_FOUND" if file does not exist
        - "EMPTY_FILE" if stat.st_size == 0
        - "INVALID_JSON: <error>" if json parsing fails
        """
        if not path.exists():
            return "NOT_FOUND"

        try:
            stat = path.stat()
        except OSError:
            return "NOT_FOUND"

        if stat.st_size == 0:
            return "EMPTY_FILE"

        if path.suffix.lower() == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                return f"INVALID_JSON: {e}"
            except (UnicodeDecodeError, OSError) as e:
                return f"INVALID_JSON: {e}"

        return None

    def verify(self, deliverables: Union[str, list[str]]) -> DeliverableVerificationResult:
        """
        Returns DeliverableVerificationResult(passed, missing_items, reasons).
        In dry-run mode always returns DeliverableVerificationResult(True, [], {}) — nothing was produced.
        For concrete file deliverables (with extension/path), verifies existence on disk,
        non-zero size, and JSON validity for .json files.
        """
        if isinstance(deliverables, str):
            deliverables = [deliverables]

        if self._dry_run or not deliverables:
            return DeliverableVerificationResult(passed=True, missing_items=[])

        missing: list[str] = []
        reasons: dict[str, str] = {}
        for d in deliverables:
            candidates = self._parse_deliverable_item(d)
            concrete_candidates = [
                c for c in candidates
                if ("." in c or "/" in c or "\\" in c) and not c.startswith(".")
            ]
            if not concrete_candidates:
                continue

            failed_reason: str | None = None
            for c in concrete_candidates:
                reason = self._validate_file(self._root / c)
                if reason is None:
                    failed_reason = None
                    break
                if failed_reason is None:
                    failed_reason = reason

            if failed_reason is not None:
                missing.append(d)
                reasons[d] = failed_reason

        return DeliverableVerificationResult(
            passed=(len(missing) == 0), missing_items=missing, reasons=reasons
        )
