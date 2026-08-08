"""
Governed Entry Capability Request Contract & Isolation — ORION-119.G & 119.5 Specification.
Authoritative entry request contract prohibiting target execution primitive selection by callers.
"""

from dataclasses import dataclass, field
import types
from typing import Any, Dict, Mapping, Optional

from ape.capabilities.contracts import PolicyDeniedError


def _freeze_dict(d: Any) -> Any:
    if isinstance(d, dict):
        return types.MappingProxyType({k: _freeze_dict(v) for k, v in d.items()})
    elif isinstance(d, (list, tuple)):
        return tuple(_freeze_dict(x) for x in d)
    return d


@dataclass(frozen=True)
class CapabilityRequest:
    """
    Authoritative entry request contract for governed capability execution.
    Prohibits target execution primitive or binding selection by callers or agents.
    """
    request_id: str
    capability_id: str
    input_payload: Mapping[str, Any]
    caller_identity: str
    context_id: str
    version_constraint: Optional[str] = None
    constraints: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_payload", _freeze_dict(dict(self.input_payload)))
        object.__setattr__(self, "constraints", _freeze_dict(dict(self.constraints)))
        object.__setattr__(self, "metadata", _freeze_dict(dict(self.metadata)))

        # 119.5 Invariant: Prohibit caller selection of target execution primitive or binding
        forbidden_keys = {
            "target_id",
            "tool_name",
            "primitive_id",
            "adapter_id",
            "binding_id",
            "prompt_id",
            "graph_id",
            "adapter",
            "provider",
            "execution_target",
        }
        all_keys = set(self.constraints.keys()).union(set(self.metadata.keys())).union(set(self.input_payload.keys()))

        if any(k in forbidden_keys for k in all_keys):
            raise PolicyDeniedError(
                "FORBIDDEN: Caller or agent specification of execution primitives or bindings (target_id/binding_id/provider/adapter) is strictly prohibited."
            )
