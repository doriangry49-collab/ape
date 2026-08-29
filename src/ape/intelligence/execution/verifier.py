"""
Deliverable Verifier — deterministic, no network, no LLM.

MVP rule: a task is VERIFIED if all declared deliverable file paths exist on disk.
In dry-run mode, verification is skipped (nothing was created).
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple


class DeliverableVerifier:
    def __init__(self, project_root: Path, dry_run: bool = True) -> None:
        self._root = project_root
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

    def verify(self, deliverables: list[str]) -> Tuple[bool, list[str]]:
        """
        Returns (ok, missing_items).
        In dry-run mode always returns (True, []) — nothing was produced.
        For concrete file deliverables (with extension/path), verifies existence on disk.
        """
        if self._dry_run or not deliverables:
            return True, []

        missing = []
        for d in deliverables:
            candidates = self._parse_deliverable_item(d)
            concrete_candidates = [
                c for c in candidates
                if ("." in c or "/" in c or "\\" in c) and not c.startswith(".")
            ]
            if not concrete_candidates:
                continue

            exists = any((self._root / c).exists() for c in concrete_candidates)
            if not exists:
                missing.append(d)

        return (len(missing) == 0), missing
