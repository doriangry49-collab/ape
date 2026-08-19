"""
AuthorizationSignalExtractor — Extract and classify authorization signals from prompt payloads.

PLATFORM ASSUMPTION NOTU:
Bu modül, gelen mesajın kaynağının kimlik doğrulamasını (mesajın gerçekten insan kullanıcıdan geldiğini)
chat-platform/session seviyesinde zaten sağlandığını varsayar; kendisi bir kimlik doğrulama mekanizması İCAT ETMEZ.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AuthorizationCategory(str, Enum):
    EXPLICIT_DIRECT_HUMAN_COMMAND = "EXPLICIT_DIRECT_HUMAN_COMMAND"  # VALID
    QUOTED_PROSE_TEMPLATE = "QUOTED_PROSE_TEMPLATE"                # INVALID
    HYPOTHETICAL_CONDITIONAL = "HYPOTHETICAL_CONDITIONAL"            # INVALID
    NEGATED_COMMAND = "NEGATED_COMMAND"                            # INVALID
    AGENT_SELF_GENERATED_CLAIM = "AGENT_SELF_GENERATED_CLAIM"        # INVALID
    TECHNICAL_STATUS_SIGNAL = "TECHNICAL_STATUS_SIGNAL"            # INVALID
    HISTORICAL_INTENT = "HISTORICAL_INTENT"                        # INVALID


@dataclass
class AuthorizationSignal:
    category: AuthorizationCategory
    is_valid: bool
    reason: str
    raw_text: str
    turn_type: str = "current_turn"
    sender_role: str = "user"


class AuthorizationSignalExtractor:
    """
    Extracts and classifies authorization signals from incoming turn payloads.
    Enforces Zero-Trust signal lineage verification.
    """

    @staticmethod
    def extract_signal(
        prompt_payload: str,
        is_current_turn: bool = True,
        sender_role: str = "user",
    ) -> AuthorizationSignal:
        text = (prompt_payload or "").strip()

        # 1. Lineage & Role Check: Only current turn user messages are eligible
        if not is_current_turn:
            return AuthorizationSignal(
                category=AuthorizationCategory.HISTORICAL_INTENT,
                is_valid=False,
                reason="Signal originates from historical context/summary, not current user turn.",
                raw_text=text,
                turn_type="historical",
                sender_role=sender_role,
            )

        # 2. Check for Agent Self-Generated Claim headers in context
        is_agent_claim = (
            sender_role == "assistant"
            or "HUMAN AUTHORIZATION EXECUTED" in text.upper()
            or "MERGE AUTHORIZATION APPROVED" in text.upper()
            or "MERGE READINESS" in text.upper()
        )

        if sender_role != "user" or ("HUMAN AUTHORIZATION EXECUTED" in text.upper() and "REQUEST" not in text.upper()):
            return AuthorizationSignal(
                category=AuthorizationCategory.AGENT_SELF_GENERATED_CLAIM,
                is_valid=False,
                reason="Signal originates from assistant/agent output or self-generated header claim.",
                raw_text=text,
                turn_type="current_turn",
                sender_role=sender_role,
            )

        # Check if the prompt is purely technical status or contains quoted/template prose
        # Check if the text contains explicit quotes (`...` or "...") around approval text
        is_quoted = bool(
            re.search(r"`[^`]*approved[^`]*`", text, re.IGNORECASE)
            or re.search(r'"[^"]*approved[^"]*"', text, re.IGNORECASE)
            or re.search(r"```[\s\S]*?```", text)
            or "Human authorization: APPROVED" in text
            or "Human authorization: APPROVED" in text
        )

        # Check for hypothetical / conditional indicators
        is_hypothetical = bool(
            re.search(r"\b(eğer|if|eğer ki|varsayalım|hypothetically|would|could|might|later|sonra)\b", text, re.IGNORECASE)
        )

        # Check for negation indicators
        is_negated = bool(
            re.search(r"\b(etme|yapma|sakın|don't|do not|no|never|durdur)\b", text, re.IGNORECASE)
        )

        # Check for technical status indicators without an explicit command
        is_status_only = bool(
            re.search(r"\b(ready to merge|merge readiness|all pass|test status)\b", text, re.IGNORECASE)
            and not re.search(r"\b(merge et|merge branch|git push|push origin)\b", text, re.IGNORECASE)
        )

        # Check if agent recommendation only
        is_recommendation_only = bool(
            re.search(r"\b(önerilir|tavsiye edilir|recommend merge|suggest merge)\b", text, re.IGNORECASE)
            and not re.search(r"\b(merge et|lütfen merge|onaylıyorum|approve merge)\b", text, re.IGNORECASE)
        )

        if is_quoted:
            return AuthorizationSignal(
                category=AuthorizationCategory.QUOTED_PROSE_TEMPLATE,
                is_valid=False,
                reason="Authorization signal is enclosed within quoted/template prose.",
                raw_text=text,
            )

        if is_negated:
            return AuthorizationSignal(
                category=AuthorizationCategory.NEGATED_COMMAND,
                is_valid=False,
                reason="Command contains negation (do not merge/push).",
                raw_text=text,
            )

        if is_hypothetical:
            return AuthorizationSignal(
                category=AuthorizationCategory.HYPOTHETICAL_CONDITIONAL,
                is_valid=False,
                reason="Command is conditional or hypothetical.",
                raw_text=text,
            )

        if is_status_only:
            return AuthorizationSignal(
                category=AuthorizationCategory.TECHNICAL_STATUS_SIGNAL,
                is_valid=False,
                reason="Technical status notification is not an explicit human authorization.",
                raw_text=text,
            )

        if is_recommendation_only:
            return AuthorizationSignal(
                category=AuthorizationCategory.AGENT_SELF_GENERATED_CLAIM,
                is_valid=False,
                reason="Agent recommendation is not an explicit human authorization.",
                raw_text=text,
            )

        # Check for direct explicit human command
        explicit_command_patterns = [
            r"\bmerge\b.*\b(main|master|origin)\b",
            r"\bmerge et\b",
            r"\bgit push origin main\b",
            r"\bapprove merge\b",
            r"\bhuman authorization:\s*approved\b",
            r"\bonaylıyorum\b",
        ]

        for pattern in explicit_command_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return AuthorizationSignal(
                    category=AuthorizationCategory.EXPLICIT_DIRECT_HUMAN_COMMAND,
                    is_valid=True,
                    reason="Explicit direct human command extracted from current turn.",
                    raw_text=text,
                )

        return AuthorizationSignal(
            category=AuthorizationCategory.QUOTED_PROSE_TEMPLATE,
            is_valid=False,
            reason="No explicit human command detected in current turn payload.",
            raw_text=text,
        )
