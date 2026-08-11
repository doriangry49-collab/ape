"""
Decoupled Prompt Pipeline Engine — ORION-111A Specification.
Provides PromptContext, PromptContextBuilder, PromptValidator, dual SHA-256 PromptRenderer,
deterministic trace_id generation, and RenderedPrompt payload.
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ape.prompts.registry import PromptTemplate


@dataclass(frozen=True)
class PromptContext:
    """Immutable prompt context container holding validated variable substitutions."""
    template_id: str
    variables: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PromptTrace:
    """Structured execution trace record for prompt rendering (isolated from LLM response)."""
    trace_id: str
    prompt_id: str
    version: str
    template_sha256: str
    rendered_sha256: str
    render_time_seconds: float
    variables: Dict[str, Any]
    renderer_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "prompt_id": self.prompt_id,
            "version": self.version,
            "template_sha256": self.template_sha256,
            "rendered_sha256": self.rendered_sha256,
            "render_time_seconds": self.render_time_seconds,
            "variables": self.variables,
            "renderer_version": self.renderer_version,
        }


@dataclass(frozen=True)
class RenderedPrompt:
    """Immutable rendered prompt payload delivered to LLM provider adapters."""
    system_prompt: str
    user_prompt: str
    prompt_id: str
    version: str
    template_sha256: str
    rendered_sha256: str
    trace_id: str


class PromptValidator:
    """Validates prompt variables against PromptTemplate schema."""

    def validate(self, template: PromptTemplate, variables: Dict[str, Any]) -> List[str]:
        """Verify variable completeness and detect missing variables."""
        errors = []
        expected_vars = template.metadata.variables

        for expected in expected_vars:
            if expected not in variables:
                errors.append(f"Missing required prompt variable: '{expected}' for template '{template.prompt_id}'.")

        return errors


class PromptContextBuilder:
    """Validates variables and constructs immutable PromptContext objects."""

    def __init__(self, validator: Optional[PromptValidator] = None) -> None:
        self.validator = validator or PromptValidator()

    def build_context(self, template: PromptTemplate, variables: Dict[str, Any]) -> PromptContext:
        """Build validated immutable PromptContext."""
        errors = self.validator.validate(template, variables)
        if errors:
            raise ValueError(f"PromptContextBuilder Error: {'; '.join(errors)}")
        return PromptContext(template_id=template.prompt_id, variables=dict(variables))


class PromptRenderer:
    """
    Pure I/O-free Prompt Renderer computing dual SHA-256 fingerprints (template_sha256 & rendered_sha256),
    deterministic trace_id, and returning RenderedPrompt + PromptTrace.
    """

    RENDERER_VERSION: str = "1.0.0"

    def render(self, template: PromptTemplate, context: PromptContext) -> Tuple[RenderedPrompt, PromptTrace]:
        """Render template with context into RenderedPrompt and PromptTrace."""
        start_time = time.time()

        sys_rendered = template.system_template
        usr_rendered = template.user_template

        for k, v in context.variables.items():
            placeholder = f"{{{k}}}"
            sys_rendered = sys_rendered.replace(placeholder, str(v))
            usr_rendered = usr_rendered.replace(placeholder, str(v))

        # Calculate rendered SHA-256 fingerprint hash
        combined_text = f"SYS:{sys_rendered}\nUSR:{usr_rendered}"
        hasher = hashlib.sha256()
        hasher.update(combined_text.encode("utf-8"))
        rendered_sha256 = hasher.hexdigest()

        # Calculate deterministic trace_id
        timestamp_str = f"{start_time:.4f}"
        trace_seed = f"{template.prompt_id}:{template.metadata.version}:{rendered_sha256}:{timestamp_str}"
        trace_hasher = hashlib.sha256()
        trace_hasher.update(trace_seed.encode("utf-8"))
        trace_id = trace_hasher.hexdigest()[:16]

        render_duration = round(time.time() - start_time, 4)

        trace = PromptTrace(
            trace_id=trace_id,
            prompt_id=template.prompt_id,
            version=str(template.metadata.version),
            template_sha256=template.template_sha256,
            rendered_sha256=rendered_sha256,
            render_time_seconds=render_duration,
            variables=dict(context.variables),
            renderer_version=self.RENDERER_VERSION,
        )

        rendered_prompt = RenderedPrompt(
            system_prompt=sys_rendered,
            user_prompt=usr_rendered,
            prompt_id=template.prompt_id,
            version=str(template.metadata.version),
            template_sha256=template.template_sha256,
            rendered_sha256=rendered_sha256,
            trace_id=trace_id,
        )

        return rendered_prompt, trace
