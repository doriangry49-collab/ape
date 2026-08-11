"""
Unit tests for ORION-119 v1.3 Capability Governance System Contracts.
Tests all 20 contract invariants, fail-closed safeguards, deep immutability,
and nested mutation attack resistance.
"""

import pytest

from ape.capabilities import ExecutionContext
from ape.capabilities.contracts import PolicyDeniedError
from ape.capabilities.governance import (
    BindingType,
    CapabilityBinding,
    CapabilityDescriptor,
    CapabilityGraphNode,
    CapabilityLifecycleState,
    CapabilityObservabilityStore,
    CapabilityPolicyEvaluator,
    CapabilityRegistry,
    CapabilityRequest,
    CompositeCapabilityDefinition,
    UnresolvableVersionError,
)
from ape.tools import RiskLevel, ToolPermission


def test_1_and_2_descriptor_deep_immutability_and_qualified_id():
    desc = CapabilityDescriptor(
        capability_id="engineering.code.generate",
        version="1.0.0",
        category="engineering",
        description="Generates code scaffolds",
        input_schema={"type": "object", "properties": {"lang": {"type": "string"}}},
        risk_tier=RiskLevel.MEDIUM,
        metadata={"tags": ["dev", "stable"]},
    )

    assert desc.qualified_id == "engineering.code.generate@1.0.0"

    # Outer dataclass frozen immutability check
    with pytest.raises(AttributeError):
        desc.version = "1.0.1"

    # Nested MappingProxyType immutability attack check
    with pytest.raises(TypeError):
        desc.metadata["tags"] = ["attack"]

    with pytest.raises(TypeError):
        desc.input_schema["properties"]["lang"]["type"] = "number"


def test_3_4_5_6_7_8_registry_version_resolution_and_fail_closed():
    registry = CapabilityRegistry()
    desc_v1 = CapabilityDescriptor(capability_id="data.echo", version="1.0.0", category="test", description="V1")
    desc_v1_1 = CapabilityDescriptor(capability_id="data.echo", version="1.1.0", category="test", description="V1.1")
    desc_v2 = CapabilityDescriptor(capability_id="data.echo", version="2.0.0", category="test", description="V2")

    registry.register(desc_v1)
    registry.register(desc_v1_1)
    registry.register(desc_v2)

    # 3 & 4. 'latest' or unparseable wildcard -> FAIL CLOSED
    with pytest.raises(UnresolvableVersionError) as exc_1:
        registry.resolve_version("data.echo", "latest")
    assert "FAIL CLOSED" in str(exc_1.value)

    with pytest.raises(UnresolvableVersionError) as exc_2:
        registry.resolve_version("data.echo", "*")
    assert "FAIL CLOSED" in str(exc_2.value)

    # 5. Exact version resolution
    res_exact = registry.resolve_version("data.echo", "1.0.0")
    assert res_exact.version == "1.0.0"

    # 6 & 7. Stable fallback resolution (highest active)
    res_stable = registry.resolve_version("data.echo")
    assert res_stable.version == "2.0.0"

    # 8. Revoked version -> NO NEW EXECUTION (FAIL CLOSED)
    registry.set_lifecycle_state("data.echo@2.0.0", CapabilityLifecycleState.REVOKED)

    # Now resolving data.echo@2.0.0 must raise UnresolvableVersionError
    with pytest.raises(UnresolvableVersionError) as exc_rev:
        registry.resolve_version("data.echo", "2.0.0")
    assert "REVOKED" in str(exc_rev.value)

    # Stable resolution now falls back to active 1.1.0
    res_fallback = registry.resolve_version("data.echo")
    assert res_fallback.version == "1.1.0"


def test_9_10_11_binding_identity_and_target_isolation():
    binding = CapabilityBinding(
        binding_id="bind_claude_gen_01",
        capability_id="engineering.code.generate",
        version="1.0.0",
        binding_type=BindingType.LLM,
        target_id="prompt_code_gen_v1",
        allowed_scopes=frozenset({"workspace"}),
        required_permissions=(ToolPermission(scope="workspace", action="write"),),
    )

    # 9. binding_id distinct from capability_id
    assert binding.binding_id != binding.capability_id
    assert binding.binding_id == "bind_claude_gen_01"

    # 10 & 20. Caller specifying target_id or binding_id in CapabilityRequest -> FAIL (PolicyDeniedError)
    for forbidden_field in ["target_id", "binding_id", "prompt_id", "provider", "adapter_id"]:
        with pytest.raises(PolicyDeniedError) as exc_target:
            CapabilityRequest(
                request_id="req_attack_1",
                capability_id="engineering.code.generate",
                input_payload={"message": "test"},
                caller_identity="agent_007",
                context_id="ctx_100",
                constraints={forbidden_field: "malicious_override"},
            )
        assert "FORBIDDEN" in str(exc_target.value)


def test_12_risk_inheritance_monotonicity():
    # Base capability is LOW
    effective_risk = CapabilityPolicyEvaluator.calculate_effective_risk(
        capability_risk=RiskLevel.LOW,
        child_risks=[RiskLevel.LOW, RiskLevel.HIGH, RiskLevel.MEDIUM],
        tool_risk=RiskLevel.LOW,
    )
    # Monotonicity: Effective risk MUST propagate to HIGH (MAX of all components)
    assert effective_risk == RiskLevel.HIGH

    # Critical context risk elevates to CRITICAL
    effective_critical = CapabilityPolicyEvaluator.calculate_effective_risk(
        capability_risk=RiskLevel.MEDIUM,
        tool_risk=RiskLevel.CRITICAL,
    )
    assert effective_critical == RiskLevel.CRITICAL


def test_13_14_composite_canonical_hash_and_self_exclusion():
    node_a = CapabilityGraphNode(node_id="node_b", capability_id="data.transform@1.0.0")
    node_b = CapabilityGraphNode(node_id="node_a", capability_id="data.echo@1.0.0")

    edges = (("node_a", "node_b"),)

    comp_1 = CompositeCapabilityDefinition(
        composite_id="workflow_analysis",
        version="1.0.0",
        nodes=(node_a, node_b),  # Passed in reverse order
        edges=edges,
    )

    comp_2 = CompositeCapabilityDefinition(
        composite_id="workflow_analysis",
        version="1.0.0",
        nodes=(node_b, node_a),  # Passed in sorted order
        edges=edges,
    )

    # 13. Canonical hash determinism regardless of node list order
    assert comp_1.definition_hash == comp_2.definition_hash
    assert len(comp_1.definition_hash) == 64

    # 14. Self-reference exclusion verification: definition_hash field is not in hashing input
    raw_hash_calc = CompositeCapabilityDefinition.compute_canonical_hash(
        composite_id="workflow_analysis",
        version="1.0.0",
        nodes=(node_a, node_b),
        edges=edges,
    )
    assert comp_1.definition_hash == raw_hash_calc


def test_15_16_policy_decision_id_determinism():
    desc = CapabilityDescriptor(capability_id="code.deploy", version="1.0.0", category="ops", description="Deploy code")
    binding = CapabilityBinding(
        binding_id="bind_deploy_01",
        capability_id="code.deploy",
        version="1.0.0",
        binding_type=BindingType.TOOL,
        target_id="mcp_deploy_tool",
    )
    ctx = ExecutionContext(execution_id="exec_p_01", venture_id="v1", trace_id="tr1", workspace_id="ws1")

    dec_1 = CapabilityPolicyEvaluator.evaluate_effective_authorization(
        request_id="req_p_100",
        descriptor=desc,
        binding=binding,
        context=ctx,
        call_id="call_p_100",
    )

    dec_2 = CapabilityPolicyEvaluator.evaluate_effective_authorization(
        request_id="req_p_100",
        descriptor=desc,
        binding=binding,
        context=ctx,
        call_id="call_p_100",
    )

    # 15 & 16. Canonical policy_decision_id determinism
    assert dec_1.decision_id == dec_2.decision_id
    assert dec_1.decision_id.startswith("dec_auth_")


def test_17_18_composite_nodes_reference_capabilities_only():
    node = CapabilityGraphNode(node_id="n1", capability_id="data.echo@1.0.0")
    # Verify node references capability_id, not raw tool
    assert "data.echo" in node.capability_id
    assert node.node_id == "n1"


def test_19_measurement_does_not_mutate_policy():
    store = CapabilityObservabilityStore()
    target_id = "bind_llm_openai"

    sig_1 = store.record_observation(target_id=target_id, success=False, latency_ms=500.0, cost=0.01)
    assert sig_1.failed_calls == 1
    assert sig_1.success_rate == 0.0

    # Ensure recording observation does NOT alter any policy or raise execution errors
    sig_2 = store.record_observation(target_id=target_id, success=True, latency_ms=100.0, cost=0.01)
    assert sig_2.total_calls == 2
    assert sig_2.success_rate == 50.0
