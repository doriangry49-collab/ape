"""
ValidatorRegistry — Dynamic Quality OS Validator Registry & Discovery Engine.
Allows registering and discovering validators by language pack and domain capabilities.
"""

from typing import Dict, List

from ape.quality.contracts import Validator
from ape.quality.validators.dependency_validator import DependencyValidator
from ape.quality.validators.import_validator import ImportValidator
from ape.quality.validators.packaging_validator import PackagingValidator
from ape.quality.validators.pytest_validator import PytestValidator
from ape.quality.validators.runtime_validator import RuntimeValidator
from ape.quality.validators.security_validator import SecurityValidator
from ape.quality.validators.smoke_validator import SmokeValidator
from ape.quality.validators.syntax import SyntaxValidator


class ValidatorRegistry:
    """Registry engine for discovering and managing Quality OS validators by language pack."""

    def __init__(self) -> None:
        self._registry: Dict[str, List[Validator]] = {}
        # Pre-register default Python language pack
        self.register("python", SyntaxValidator())
        self.register("python", ImportValidator())
        self.register("python", DependencyValidator())
        self.register("python", PackagingValidator())
        self.register("python", SecurityValidator())
        self.register("python", PytestValidator())
        self.register("python", SmokeValidator())
        self.register("python", RuntimeValidator())

    def register(self, language: str, validator: Validator) -> None:
        """Register a validator under a specific language or domain capability pack."""
        lang_key = language.lower().strip()
        if lang_key not in self._registry:
            self._registry[lang_key] = []
        # Prevent duplicate registration by name
        existing_names = {v.name for v in self._registry[lang_key]}
        if validator.name not in existing_names:
            self._registry[lang_key].append(validator)

    def discover(self, language: str = "python") -> List[Validator]:
        """Discover all registered validators for the given language pack."""
        lang_key = language.lower().strip()
        return list(self._registry.get(lang_key, []))

    def get_validators(self, language: str = "python") -> List[Validator]:
        """Alias for discover(), returns all validators for a language pack."""
        return self.discover(language=language)


def get_default_registry() -> ValidatorRegistry:
    """Returns global default registry instance."""
    return default_registry


# Global default registry instance
default_registry = ValidatorRegistry()
