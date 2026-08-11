"""
Enterprise Auth & Key Manager Engine — EPIC G6-2 Specification.
Provides JWT authentication token generation and API key management.
"""

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class TokenClaims:
    """JWT Token claims wrapper."""
    sub: str
    role: str  # ADMIN, DEVELOPER, AUDITOR
    workspace_slug: str
    exp: float


class JWTAuthEngine:
    """Enterprise HMAC SHA-256 JWT Authentication Token Engine."""

    def __init__(self, secret_key: str = "ape_enterprise_secret_key_2026") -> None:
        self.secret_key = secret_key.encode("utf-8")

    def create_token(self, sub: str, role: str, workspace_slug: str = "default", ttl_seconds: float = 3600.0) -> str:
        """Create HMAC SHA-256 signed JWT token."""
        header = json.dumps({"alg": "HS256", "typ": "JWT"}).encode("utf-8")
        claims = json.dumps({
            "sub": sub,
            "role": role,
            "workspace_slug": workspace_slug,
            "exp": time.time() + ttl_seconds,
        }).encode("utf-8")

        import base64
        h_b64 = base64.urlsafe_b64encode(header).decode().rstrip("=")
        c_b64 = base64.urlsafe_b64encode(claims).decode().rstrip("=")

        payload_msg = f"{h_b64}.{c_b64}".encode("utf-8")
        sig = hmac.new(self.secret_key, payload_msg, hashlib.sha256).digest()
        s_b64 = base64.urlsafe_b64encode(sig).decode().rstrip("=")

        return f"{h_b64}.{c_b64}.{s_b64}"

    def decode_token(self, token: str) -> Optional[TokenClaims]:
        """Verify HMAC signature and decode TokenClaims."""
        import base64
        parts = token.split(".")
        if len(parts) != 3:
            return None

        h_b64, c_b64, s_b64 = parts
        payload_msg = f"{h_b64}.{c_b64}".encode("utf-8")
        expected_sig = hmac.new(self.secret_key, payload_msg, hashlib.sha256).digest()

        # Re-add padding
        s_b64_pad = s_b64 + "=" * (-len(s_b64) % 4)
        provided_sig = base64.urlsafe_b64decode(s_b64_pad)

        if not hmac.compare_digest(provided_sig, expected_sig):
            return None

        c_b64_pad = c_b64 + "=" * (-len(c_b64) % 4)
        c_data = json.loads(base64.urlsafe_b64decode(c_b64_pad).decode("utf-8"))

        if time.time() > c_data.get("exp", 0):
            return None  # Expired token

        return TokenClaims(
            sub=c_data["sub"],
            role=c_data["role"],
            workspace_slug=c_data["workspace_slug"],
            exp=c_data["exp"],
        )
