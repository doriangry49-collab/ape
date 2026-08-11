"""
Plugin SDK Manifest Data Structures — RFC-022 / PR-P1 Specification.
Defines PluginManifest structure for declarative plugin configuration.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PluginManifest:
    """Declarative plugin manifest structure."""
    name: str
    version: str
    api_version: str = "1"
    description: str = ""
    author: str = ""
    license: str = "MIT"
    entrypoint: str = ""
    requires: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "api_version": self.api_version,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "entrypoint": self.entrypoint,
            "requires": self.requires,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginManifest":
        return cls(
            name=str(data.get("name", "unknown")),
            version=str(data.get("version", "0.1.0")),
            api_version=str(data.get("api_version", "1")),
            description=str(data.get("description", "")),
            author=str(data.get("author", "")),
            license=str(data.get("license", "MIT")),
            entrypoint=str(data.get("entrypoint", "")),
            requires=list(data.get("requires", [])),
            metadata=dict(data.get("metadata", {})),
        )
