"""
File-Based Immutable Prompt Registry & Metadata Specification — ORION-111A.
Loads standardized YAML prompt templates from disk, tracks SemVer PromptVersion objects,
and freezes into an immutable read-only registry at startup.
"""

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
import yaml


@dataclass(frozen=True)
class PromptVersion:
    """Immutable SemVer prompt version dataclass."""
    major: int = 1
    minor: int = 0
    patch: int = 0
    created_at: float = field(default_factory=time.time)
    deprecated: bool = False

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptVersion":
        if isinstance(data, dict):
            return cls(
                major=data.get("major", 1),
                minor=data.get("minor", 0),
                patch=data.get("patch", 0),
                deprecated=data.get("deprecated", False),
            )
        return cls()


@dataclass
class PromptMetadata:
    """Standardized Prompt Metadata schema matching YAML template header."""
    id: str
    version: PromptVersion
    owner: str = "general"
    runtime_min: str = "0.1.0"
    runtime_max: str = "2.x"
    variables: List[str] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class PromptTemplate:
    """Prompt template object holding metadata, unrendered system & user texts, and template SHA-256."""
    metadata: PromptMetadata
    system_template: str
    user_template: str
    template_sha256: str

    @property
    def prompt_id(self) -> str:
        return self.metadata.id


class PromptRegistry:
    """
    Dependency-injection file-based Prompt Registry.
    Loads YAML templates from disk and locks into an immutable read-only state via freeze().
    """

    def __init__(self) -> None:
        self._templates: Dict[str, PromptTemplate] = {}
        self._frozen: bool = False

    def is_frozen(self) -> bool:
        return self._frozen

    def freeze(self) -> None:
        """Freeze registry to prevent further registration and enforce immutability."""
        self._frozen = True

    def register(self, template: PromptTemplate) -> None:
        """Register a PromptTemplate. Raises RuntimeError if frozen."""
        if self._frozen:
            raise RuntimeError("Cannot register new template: PromptRegistry is frozen (read-only).")
        self._templates[template.prompt_id] = template

    def get(self, prompt_id: str) -> PromptTemplate:
        """Fetch PromptTemplate by canonical prompt_id slug."""
        if prompt_id not in self._templates:
            raise KeyError(f"Prompt template '{prompt_id}' not found in PromptRegistry.")
        return self._templates[prompt_id]

    def has(self, prompt_id: str) -> bool:
        return prompt_id in self._templates

    def list_prompts(self) -> List[str]:
        return sorted(list(self._templates.keys()))

    @classmethod
    def load_from_directory(cls, templates_dir: Path) -> "PromptRegistry":
        """
        Scan directory for *.yaml prompt templates, parse YAML metadata,
        calculate template_sha256, build PromptRegistry, and freeze it.
        """
        registry = cls()
        templates_dir = Path(templates_dir)

        if not templates_dir.exists():
            registry.freeze()
            return registry

        for yaml_path in sorted(list(templates_dir.glob("**/*.yaml"))):
            try:
                raw_text = yaml_path.read_text(encoding="utf-8")
                doc = yaml.safe_load(raw_text) or {}

                p_id = doc.get("id")
                if not p_id:
                    continue

                version_obj = PromptVersion.from_dict(doc.get("version", {}))
                runtime_doc = doc.get("runtime", {})

                meta = PromptMetadata(
                    id=p_id,
                    version=version_obj,
                    owner=doc.get("owner", "general"),
                    runtime_min=runtime_doc.get("min", "0.1.0"),
                    runtime_max=runtime_doc.get("max", "2.x"),
                    variables=doc.get("variables", []),
                    includes=doc.get("includes", []),
                    tags=doc.get("tags", []),
                )

                sys_tmpl = doc.get("system", "").strip()
                usr_tmpl = doc.get("user", "").strip()

                # Calculate template SHA-256 hash (unrendered text)
                hasher = hashlib.sha256()
                hasher.update(raw_text.encode("utf-8"))
                template_sha256 = hasher.hexdigest()

                tmpl = PromptTemplate(
                    metadata=meta,
                    system_template=sys_tmpl,
                    user_template=usr_tmpl,
                    template_sha256=template_sha256,
                )
                registry.register(tmpl)

            except Exception:
                continue

        registry.freeze()
        return registry
