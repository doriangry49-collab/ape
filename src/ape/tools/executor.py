"""
ToolExecutor & 7-Stage Lifecycle Orchestrator — ORION-117.0 Specification.
Orchestrates DISCOVER -> REGISTER -> AUTHORIZE -> RESOLVE -> EXECUTE -> RESULT -> EVIDENCE.
"""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional

from ape.tools.adapters.base import BaseToolAdapter
from ape.tools.contracts import (
    ApprovalRequiredError,
    EvidenceSink,
    ToolAuthorizationError,
    ToolCallPayload,
    ToolExecutionError,
    ToolLifecycleStage,
    ToolResult,
)
from ape.tools.definition import ToolDefinition
from ape.tools.policy import PolicyDecision, ToolPolicyEvaluator
from ape.tools.registry import ToolRegistry


class DefaultEvidenceSink:
    """In-memory default EvidenceSink implementation computing SHA-256 evidence hashes."""

    def __init__(self) -> None:
        self.events: List[Dict[str, str]] = []

    def emit_evidence(self, stage: ToolLifecycleStage, event_data: Dict[str, str]) -> str:
        payload_str = json.dumps(event_data, sort_keys=True)
        evidence_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        self.events.append({"stage": stage.value, "hash": evidence_hash, "data": payload_str})
        return evidence_hash


class ToolExecutor:
    """7-Stage Lifecycle Orchestrator executing tools across DISCOVER -> REGISTER -> AUTHORIZE -> RESOLVE -> EXECUTE -> RESULT -> EVIDENCE."""

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        policy_evaluator: Optional[ToolPolicyEvaluator] = None,
        evidence_sink: Optional[EvidenceSink] = None,
    ) -> None:
        self.registry = registry or ToolRegistry()
        self.policy_evaluator = policy_evaluator or ToolPolicyEvaluator()
        self.evidence_sink = evidence_sink or DefaultEvidenceSink()
        self._adapters: Dict[str, BaseToolAdapter] = {}

    def register_adapter(self, adapter: BaseToolAdapter) -> None:
        """Register an adapter and automatically register all tools exposed by it (DISCOVER -> REGISTER stages)."""
        tools = adapter.list_tools()
        for tool_def in tools:
            self.registry.register_tool(tool_def)
            self._adapters[tool_def.name] = adapter

    def execute(
        self,
        payload: ToolCallPayload,
        context_permissions: Optional[List[Any]] = None,
        approved_by_human: bool = False,
    ) -> ToolResult:
        """Execute a ToolCallPayload through the full 7-stage lifecycle."""
        start_time = time.time()

        # 1. DISCOVER & 2. REGISTER
        self.evidence_sink.emit_evidence(ToolLifecycleStage.DISCOVER, {"call_id": payload.call_id, "tool_name": payload.tool_name})
        tool_def = self.registry.resolve_tool(payload.tool_name, version=payload.tool_version)
        self.evidence_sink.emit_evidence(ToolLifecycleStage.REGISTER, {"tool_name": tool_def.name, "version": tool_def.version})

        # 3. AUTHORIZE
        auth_res = self.policy_evaluator.evaluate(tool_def, context_permissions=context_permissions, approved_by_human=approved_by_human)
        self.evidence_sink.emit_evidence(ToolLifecycleStage.AUTHORIZE, {"tool_name": tool_def.name, "decision": auth_res.decision.value})

        if auth_res.decision == PolicyDecision.DENIED:
            raise ToolAuthorizationError(f"Tool execution denied: {auth_res.reason}")
        if auth_res.decision == PolicyDecision.APPROVAL_REQUIRED:
            raise ApprovalRequiredError(f"Tool execution requires human approval: {auth_res.reason}")

        # 4. RESOLVE
        if payload.tool_name not in self._adapters:
            raise ToolExecutionError(f"No adapter registered to handle tool '{payload.tool_name}'.")
        adapter = self._adapters[payload.tool_name]
        self.evidence_sink.emit_evidence(ToolLifecycleStage.RESOLVE, {"adapter": adapter.__class__.__name__})

        # 5. EXECUTE
        self.evidence_sink.emit_evidence(ToolLifecycleStage.EXECUTE, {"call_id": payload.call_id})
        try:
            raw_result = adapter.execute_tool(payload)
        except Exception as err:
            dur_ms = round((time.time() - start_time) * 1000.0, 2)
            ev_hash = self.evidence_sink.emit_evidence(ToolLifecycleStage.RESULT, {"error": str(err)})
            return ToolResult(
                call_id=payload.call_id,
                tool_name=payload.tool_name,
                success=False,
                error_message=str(err),
                duration_ms=dur_ms,
                evidence_hash=ev_hash,
            )

        # 6. RESULT
        dur_ms = round((time.time() - start_time) * 1000.0, 2)
        ev_hash = self.evidence_sink.emit_evidence(
            ToolLifecycleStage.RESULT,
            {"call_id": payload.call_id, "success": str(raw_result.success)},
        )

        # 7. EVIDENCE
        final_result = ToolResult(
            call_id=payload.call_id,
            tool_name=payload.tool_name,
            success=raw_result.success,
            output_data=raw_result.output_data,
            error_message=raw_result.error_message,
            duration_ms=dur_ms,
            evidence_hash=ev_hash,
            metadata=raw_result.metadata,
        )
        self.evidence_sink.emit_evidence(ToolLifecycleStage.EVIDENCE, {"evidence_hash": ev_hash})

        return final_result
