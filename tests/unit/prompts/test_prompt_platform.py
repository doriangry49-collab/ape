"""
Unit tests for ORION-111A Prompt Platform Core & Registry.
Verifies file-based YAML template loading, startup registry freezing (read-only immutability),
PromptContextBuilder variable validation, pure I/O-free PromptRenderer dual SHA-256 fingerprinting,
deterministic trace_id generation, and isolated PromptTraceStore disk saving.
"""

from pathlib import Path
import tempfile
import pytest

from ape.prompts import (
    PromptContextBuilder,
    PromptRegistry,
    PromptRenderer,
    PromptTemplate,
    PromptTraceStore,
    RenderedPrompt,
)


def test_file_based_prompt_registry_loading_and_freezing():
    templates_dir = Path(__file__).parents[3] / "src" / "ape" / "prompts" / "templates"
    registry = PromptRegistry.load_from_directory(templates_dir)

    assert registry.is_frozen()
    assert registry.has("research.market_analysis")
    assert registry.has("engineering.nextjs_blueprint")
    assert registry.has("marketing.landing_page")
    assert registry.has("publishing.release_notes")

    # Read-only immutability test
    tmpl = registry.get("research.market_analysis")
    with pytest.raises(RuntimeError) as exc_info:
        registry.register(tmpl)
    assert "PromptRegistry is frozen" in str(exc_info.value)


def test_prompt_context_builder_variable_validation():
    templates_dir = Path(__file__).parents[3] / "src" / "ape" / "prompts" / "templates"
    registry = PromptRegistry.load_from_directory(templates_dir)
    tmpl = registry.get("engineering.nextjs_blueprint")

    builder = PromptContextBuilder()

    # Valid context building
    ctx = builder.build_context(tmpl, {"project_name": "SaaS Platform", "stack": "Next.js 14"})
    assert ctx.template_id == "engineering.nextjs_blueprint"
    assert ctx.variables["project_name"] == "SaaS Platform"

    # Missing variable validation test
    with pytest.raises(ValueError) as exc_info:
        builder.build_context(tmpl, {"project_name": "SaaS Platform"})
    assert "Missing required prompt variable: 'stack'" in str(exc_info.value)


def test_prompt_renderer_dual_sha256_and_deterministic_trace_id():
    templates_dir = Path(__file__).parents[3] / "src" / "ape" / "prompts" / "templates"
    registry = PromptRegistry.load_from_directory(templates_dir)
    tmpl = registry.get("marketing.landing_page")

    builder = PromptContextBuilder()
    ctx = builder.build_context(tmpl, {"product_name": "AI CRM Bot", "value_prop": "Automate leads in 5 minutes"})

    renderer = PromptRenderer()
    rendered_prompt, trace = renderer.render(tmpl, ctx)

    assert isinstance(rendered_prompt, RenderedPrompt)
    assert len(rendered_prompt.template_sha256) == 64
    assert len(rendered_prompt.rendered_sha256) == 64
    assert rendered_prompt.template_sha256 != rendered_prompt.rendered_sha256
    assert len(rendered_prompt.trace_id) == 16
    assert trace.trace_id == rendered_prompt.trace_id
    assert "AI CRM Bot" in rendered_prompt.user_prompt


def test_isolated_prompt_trace_store_saving():
    templates_dir = Path(__file__).parents[3] / "src" / "ape" / "prompts" / "templates"
    registry = PromptRegistry.load_from_directory(templates_dir)
    tmpl = registry.get("publishing.release_notes")

    builder = PromptContextBuilder()
    ctx = builder.build_context(tmpl, {"venture_name": "RealEstate OS", "deploy_url": "https://realestate.ape.dev"})

    renderer = PromptRenderer()
    rendered_prompt, trace = renderer.render(tmpl, ctx)

    with tempfile.TemporaryDirectory() as tmp_dir:
        store = PromptTraceStore(root_dir=Path(tmp_dir) / "ventures")
        trace_path = store.save_trace("v_realestate_001", trace)

        assert trace_path.exists()
        assert trace_path.name == f"{trace.trace_id}.json"
        assert trace_path.parent.name == "prompt"
        assert trace_path.parent.parent.name == "traces"

        loaded = store.load_trace("v_realestate_001", trace.trace_id)
        assert loaded["prompt_id"] == "publishing.release_notes"
        assert loaded["rendered_sha256"] == rendered_prompt.rendered_sha256
