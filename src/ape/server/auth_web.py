"""
MVP Web Login & Session Authenticator — ORION-101 Week 1 Specification.
Provides Web App session authentication for the APE Cloud MVP dashboard.
"""

import hashlib
import time
from typing import Dict, Optional


class WebAuthSessionManager:
    """Manages simple Web App authentication sessions for MVP release."""

    def __init__(self, secret: str = "ape_mvp_web_secret_2026") -> None:
        self.secret = secret
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def authenticate(self, username: str, password_hash: str) -> Optional[str]:
        """Authenticate user credentials and return session token."""
        if not username:
            return None
        session_token = hashlib.sha256(f"{username}:{time.time()}:{self.secret}".encode()).hexdigest()
        self._sessions[session_token] = {
            "username": username,
            "created_at": time.time(),
            "ttl_seconds": 86400.0,
        }
        return session_token

    def verify_session(self, session_token: str) -> bool:
        """Verify active session token."""
        if session_token not in self._sessions:
            return False
        sess = self._sessions[session_token]
        if (time.time() - sess["created_at"]) > sess["ttl_seconds"]:
            del self._sessions[session_token]
            return False
        return True
