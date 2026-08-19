"""
ExecutionAuthToken — Cryptographic Authorization Token for Sandbox Execution.
SPEC-0014 / ORION-146 Specification.

Untrusted callers cannot produce valid HMAC signatures without secret_key.
Boundary Note:
Untrusted code executing inside the same Python process can access module variables;
the HMAC signature provides cryptographic authenticity of the token issued by PolicyGateStage.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

# Process-local secret key used ONLY in non-production (dev/test) mode when APE_GOVERNANCE_SECRET is unset.
_DEV_LOCAL_SECRET: bytes = secrets.token_bytes(32)


def get_governance_secret() -> bytes:
    """
    Retrieves the governance HMAC secret key.
    - PRODUCTION MODE (APE_ENV=production or NODE_ENV=production): Requires APE_GOVERNANCE_SECRET env var.
      Fails-closed with RuntimeError if missing.
    - DEV/TEST MODE: Uses APE_GOVERNANCE_SECRET if set, otherwise falls back to process-local random secret.
    """
    env_val = os.environ.get("APE_GOVERNANCE_SECRET")
    is_production = (
        os.environ.get("APE_ENV") == "production"
        or os.environ.get("NODE_ENV") == "production"
    )

    if is_production:
        if not env_val:
            raise RuntimeError(
                "Production environment requires APE_GOVERNANCE_SECRET environment variable."
            )
        return env_val.encode("utf-8")

    if env_val:
        return env_val.encode("utf-8")

    return _DEV_LOCAL_SECRET


@dataclass(frozen=True)
class ExecutionAuthToken:
    """
    Cryptographic authorization token issued strictly by PolicyGateStage.
    """
    task_id: str
    issued_at: float
    signature: str
    issuer: str = "PolicyGateStage"

    @classmethod
    def create(cls, task_id: str, secret_key: bytes) -> ExecutionAuthToken:
        """Issues a new signed token for task_id using secret_key."""
        issued_at = datetime.now(timezone.utc).timestamp()
        issuer = "PolicyGateStage"
        msg = f"{issuer}:{task_id}:{issued_at}".encode("utf-8")
        signature = hmac.new(secret_key, msg, hashlib.sha256).hexdigest()
        return cls(
            task_id=task_id,
            issued_at=issued_at,
            signature=signature,
            issuer=issuer,
        )

    def verify(self, secret_key: bytes, max_age_seconds: float = 300.0) -> bool:
        """
        Verifies cryptographic signature and freshness / bounded lifetime.
        Freshness check: 0 <= age <= 300s (with 5s clock skew tolerance).
        """
        if self.issuer != "PolicyGateStage":
            return False

        msg = f"{self.issuer}:{self.task_id}:{self.issued_at}".encode("utf-8")
        expected_sig = hmac.new(secret_key, msg, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(self.signature, expected_sig):
            return False

        now = datetime.now(timezone.utc).timestamp()
        age = now - self.issued_at
        if age < -5.0 or age > max_age_seconds:
            return False

        return True


def create_test_auth_token(task_id: str = "test") -> ExecutionAuthToken:
    """Helper for unit tests to obtain a valid ExecutionAuthToken."""
    secret = get_governance_secret()
    return ExecutionAuthToken.create(task_id, secret)
