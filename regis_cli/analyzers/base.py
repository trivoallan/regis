"""Base class for all analyzers."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from importlib import resources
from typing import Any

import jsonschema

from regis_cli.registry.client import RegistryClient

logger = logging.getLogger(__name__)


class AnalyzerError(Exception):
    """Raised when an analyzer encounters an error."""


class BaseAnalyzer(ABC):
    """Abstract base class for registry analyzers.

    Subclasses must define :attr:`name` and :attr:`schema_file` and implement
    :meth:`analyze`.
    """

    #: Human-readable name of the analyzer.
    name: str = ""

    #: Filename of the JSON Schema inside ``regis_cli/reference/schemas/``.
    schema_file: str = ""

    @classmethod
    def default_rules(cls) -> list[dict[str, Any]]:
        """Return a list of default rules provided by this analyzer.
        Override in subclasses to provide default evaluation rules.
        """
        return []

    @abstractmethod
    def analyze(
        self,
        client: RegistryClient,
        repository: str,
        tag: str,
        platform: str | None = None,
    ) -> dict[str, Any]:
        """Run the analysis and return a report dict.

        Args:
            client: An authenticated :class:`RegistryClient`.
            repository: Full repository path (e.g. ``library/nginx``).
            tag: The image tag to analyze.

        Returns:
            A dict conforming to the analyzer's JSON Schema.
        """

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self, report: dict[str, Any]) -> None:
        """Validate *report* against this analyzer's JSON Schema.

        Args:
            report: The report dict to validate.

        Raises:
            AnalyzerError: If the report does not conform to the schema.
        """
        schema = self._load_schema()
        try:
            jsonschema.validate(instance=report, schema=schema)
        except jsonschema.ValidationError as exc:
            raise AnalyzerError(
                f"Report from analyzer '{self.name}' failed schema validation: {exc.message}"
            ) from exc

    def _load_schema(self) -> dict[str, Any]:
        """Load the JSON Schema file from the ``regis_cli.schemas`` package."""
        schema_ref = resources.files("regis_cli.schemas").joinpath(self.schema_file)
        schema_text = schema_ref.read_text(encoding="utf-8")
        return json.loads(schema_text)  # type: ignore[no-any-return]
