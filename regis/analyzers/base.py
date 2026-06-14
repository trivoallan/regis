"""Base class for all analyzers."""

from __future__ import annotations

import json
import logging
import warnings
from abc import ABC, abstractmethod
from importlib import resources
from typing import Any

import jsonschema

from regis.core.domain.errors import AnalyzerError
from regis.registry.client import RegistryClient

logger = logging.getLogger(__name__)


def _overrides_legacy_default_rules(cls: type) -> bool:
    """Return True if *cls* (or a non-base ancestor) overrides ``default_rules``.

    Used to honor third-party analyzers that only implement the deprecated
    :meth:`BaseAnalyzer.default_rules` API. Scans the MRO, ignoring
    :class:`BaseAnalyzer` itself, for a class declaring ``default_rules`` in its
    own ``__dict__``.
    """
    for klass in cls.__mro__:
        if klass is BaseAnalyzer:
            continue
        if "default_rules" in klass.__dict__:
            return True
    return False


class BaseAnalyzer(ABC):
    """Abstract base class for registry analyzers.

    Subclasses must define :attr:`name` and :attr:`schema_file` and implement
    :meth:`analyze`.
    """

    #: Human-readable name of the analyzer.
    name: str = ""

    #: Filename of the JSON Schema inside ``regis/reference/schemas/``.
    schema_file: str = ""

    #: Bridge marker (P3): True once the analyzer consumes ``analyze(ctx)``.
    #: The AnalyzeImage use-case dispatches on this during the migration; the
    #: marker and the legacy branch are removed in P3d.
    uses_context: bool = False

    @classmethod
    def default_criteria(cls) -> list[dict[str, Any]]:
        """Return the default criteria (reusable, parameterized conditions).

        This is the canonical method analyzers override to ship reusable
        criterion templates. Override in subclasses to provide defaults.

        Back-compat: a direct subclass of :class:`BaseAnalyzer` that only
        overrides the legacy :meth:`default_rules` (renamed in the rule ->
        criterion migration) is still honored. The base implementation
        delegates to ``default_rules`` *only* when a subclass has actually
        overridden it; otherwise it returns its own (empty) defaults.

        The recursion guard is essential: the deprecated :meth:`default_rules`
        shim delegates back to ``default_criteria``, so without it an analyzer
        overriding neither method would loop forever between the two. Override
        detection uses an MRO ``__dict__`` scan
        (:func:`_overrides_legacy_default_rules`) rather than the identity check
        ``cls.default_rules is not BaseAnalyzer.default_rules`` — the latter
        cannot distinguish a subclass that declared its own ``default_rules``
        from one that merely inherits the base shim, and reintroduces the
        recursion it was meant to prevent.
        """
        if _overrides_legacy_default_rules(cls):
            # External subclass overrode only the legacy method — honor it.
            # No warning here: the subclass is the one carrying the deprecated
            # API, and it is exercised at evaluation time, not here.
            return cls.default_rules()
        return []

    @classmethod
    def default_rules(cls) -> list[dict[str, Any]]:
        """Deprecated alias for :meth:`default_criteria`.

        Retained as a back-compat shim during the rule -> criterion vocabulary
        migration. Emits a :class:`DeprecationWarning` and delegates to
        :meth:`default_criteria`. Third-party plugins that override this method
        keep working (see :meth:`default_criteria`).
        """
        warnings.warn(
            "BaseAnalyzer.default_rules() is deprecated; "
            "override and call default_criteria() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return cls.default_criteria()

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
        """Load the JSON Schema file from the ``regis.schemas`` package."""
        schema_ref = resources.files("regis.schemas").joinpath(self.schema_file)
        schema_text = schema_ref.read_text(encoding="utf-8")
        return json.loads(schema_text)  # type: ignore[no-any-return]
