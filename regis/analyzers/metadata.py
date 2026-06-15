"""Metadata analyzer — validates ``--meta`` values against JSON Schema."""

from __future__ import annotations

import json
import logging
from importlib import resources
from pathlib import Path
from typing import Any

import jsonschema

from regis.analyzers.base import AnalyzerError, BaseAnalyzer
from regis.core.domain.context import AnalysisContext
from regis.utils.predicates import is_url

logger = logging.getLogger(__name__)

# A local format checker so `format: uri` is enforced deterministically
# (jsonschema's default does nothing for "uri" without an optional dependency).
_FORMAT_CHECKER = jsonschema.FormatChecker()


@_FORMAT_CHECKER.checks("uri")
def _check_uri(value: object) -> bool:
    """Validate a `format: uri` field.

    Deliberately narrowed to http/https URLs (via :func:`is_url`), which is the
    intended shape for the well-known `ci.job.url` field. This is stricter than
    RFC-3986 `uri` (no ftp/urn/mailto). Format checks run only on string
    instances; non-strings are caught by the schema's `type`.
    """
    return is_url(value) if isinstance(value, str) else True


def _collect_leaf_paths(schema: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Recursively collect dotted leaf paths from a schema's ``properties``.

    A leaf is any property that is not an object-with-properties. Returns a mapping
    of ``dotted.path -> subschema`` (subschema currently unused but kept for clarity).
    """
    paths: dict[str, Any] = {}
    for name, sub in schema.get("properties", {}).items():
        path = f"{prefix}.{name}" if prefix else name
        if (
            isinstance(sub, dict)
            and sub.get("type") == "object"
            and "properties" in sub
        ):
            paths.update(_collect_leaf_paths(sub, path))
        else:
            paths[path] = sub
    return paths


class MetadataAnalyzer(BaseAnalyzer):
    """Validate user-supplied metadata against the well-known schema and an optional playbook extension.

    Unlike other analyzers, :class:`MetadataAnalyzer` does not need a registry
    client, repository, or tag.  The inputs are provided at construction time
    and the positional arguments of :meth:`analyze` are accepted but ignored so
    the class remains compatible with :class:`BaseAnalyzer`.
    """

    name = "metadata"
    schema_file = ""  # MetadataAnalyzer validates metadata inputs, not its own output.

    def __init__(
        self,
        metadata: dict[str, Any] | None = None,
        meta_schema_path: Path | None = None,
    ) -> None:
        """Initialise the analyzer.

        Args:
            metadata: The metadata dict supplied by the user via ``--meta`` flags.
            meta_schema_path: Optional path to a ``meta.schema.json`` from a
                playbook bundle.  When the file exists its schema is merged with
                the well-known schema via ``allOf``.
        """
        self._metadata: dict[str, Any] = metadata or {}
        self._meta_schema_path = meta_schema_path

    # ------------------------------------------------------------------
    # BaseAnalyzer interface
    # ------------------------------------------------------------------

    def analyze(self, ctx: AnalysisContext | None = None) -> dict[str, Any]:
        """Validate metadata and return a result dict.

        Args:
            ctx: Ignored — accepted for the hexagonal ``analyze(ctx)`` contract.
                MetadataAnalyzer's inputs come from ``__init__`` (``--meta`` values),
                not the image context. The rerun path calls ``analyze()`` with no
                argument, so ``ctx`` stays optional.

        Returns:
            A dict with keys ``analyzer``, ``metadata``, ``metadata_validation``,
            and ``valid``.
        """
        combined_schema = self._build_combined_schema()

        # Known leaf fields (dotted) across the well-known + playbook schemas.
        leaf_paths: dict[str, Any] = {}
        for sub in combined_schema.get("allOf", []):
            leaf_paths.update(_collect_leaf_paths(sub))

        validator = jsonschema.Draft202012Validator(
            combined_schema, format_checker=_FORMAT_CHECKER
        )
        errors = list(validator.iter_errors(self._metadata))

        # metadata_validation: one entry per known leaf path, valid by default.
        metadata_validation: dict[str, Any] = {
            path: {"valid": True} for path in leaf_paths
        }
        for error in errors:
            if error.validator == "required":
                base = list(error.absolute_path)
                # Navigate to the object the `required` constraint applies to so we
                # only flag fields that are genuinely absent (validator_value lists
                # ALL required fields, including present ones).
                obj: Any = self._metadata
                for key in base:
                    obj = obj.get(key, {}) if isinstance(obj, dict) else {}
                for field in error.validator_value:
                    if isinstance(obj, dict) and field in obj:
                        continue
                    dotted = ".".join([*map(str, base), str(field)])
                    metadata_validation[dotted] = {
                        "valid": False,
                        "error": error.message,
                    }
            else:
                dotted = ".".join(str(p) for p in error.absolute_path)
                metadata_validation[dotted or "_schema"] = {
                    "valid": False,
                    "error": error.message,
                }

        return {
            "analyzer": self.name,
            "metadata": dict(self._metadata),
            "metadata_validation": metadata_validation,
            "valid": not errors,
        }

    def validate(self, report: dict[str, Any]) -> None:
        """No-op: MetadataAnalyzer validates metadata inputs, not its own output."""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_combined_schema(self) -> dict[str, Any]:
        """Build an ``allOf`` schema combining the well-known and playbook schemas."""
        well_known = self._load_well_known_schema()
        combined: dict[str, Any] = {"allOf": [well_known]}

        if self._meta_schema_path and self._meta_schema_path.exists():
            try:
                playbook_schema = json.loads(
                    self._meta_schema_path.read_text(encoding="utf-8")
                )
                combined["allOf"].append(playbook_schema)
            except (OSError, json.JSONDecodeError):
                logger.warning(
                    "Could not load playbook meta schema from %s; falling back to well-known only.",
                    self._meta_schema_path,
                )

        return combined

    @staticmethod
    def _load_well_known_schema() -> dict[str, Any]:
        """Load ``regis/schemas/meta/well-known.schema.json`` via importlib.resources."""
        try:
            schema_ref = resources.files("regis.schemas").joinpath(
                "meta/well-known.schema.json"
            )
            return json.loads(schema_ref.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
        except Exception as exc:
            raise AnalyzerError(
                f"Failed to load well-known metadata schema: {exc}"
            ) from exc
