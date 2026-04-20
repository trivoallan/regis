"""Metadata analyzer — validates ``--meta`` values against JSON Schema."""

from __future__ import annotations

import json
import logging
from importlib import resources
from pathlib import Path
from typing import Any

import jsonschema

from regis.analyzers.base import AnalyzerError, BaseAnalyzer

logger = logging.getLogger(__name__)


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

    def analyze(
        self,
        client: Any = None,
        repository: str = "",
        tag: str = "",
        platform: str | None = None,
    ) -> dict[str, Any]:
        """Validate metadata and return a result dict.

        Args:
            client: Ignored — accepted for ``BaseAnalyzer`` compatibility.
            repository: Ignored.
            tag: Ignored.
            platform: Ignored.

        Returns:
            A dict with keys ``analyzer``, ``metadata``, ``metadata_validation``,
            and ``valid``.
        """
        combined_schema = self._build_combined_schema()
        schema_properties: dict[str, Any] = {}
        required_fields: set[str] = set()
        for sub in combined_schema.get("allOf", []):
            schema_properties.update(sub.get("properties", {}))
            required_fields.update(sub.get("required", []))

        # Build per-field error map from jsonschema.
        validator = jsonschema.Draft202012Validator(combined_schema)
        field_errors: dict[str, str] = {}
        for error in validator.iter_errors(self._metadata):
            # Map the error back to the field it concerns.
            if error.path:
                field = str(error.path[0])
            elif error.validator == "required":
                # "required" errors report the missing field name in the message.
                # Extract field name from the validator_value list when possible.
                for missing in error.validator_value:
                    if missing not in self._metadata:
                        field_errors[missing] = error.message
                        break
                continue
            else:
                continue
            field_errors[field] = error.message

        # Build the output metadata dict: user-supplied values + null for schema
        # properties that are absent.
        out_metadata: dict[str, Any] = {}
        for key, value in self._metadata.items():
            out_metadata[key] = value
        for field in schema_properties:
            if field not in out_metadata:
                out_metadata[field] = None

        # Build per-field validation results — only for schema-defined properties.
        metadata_validation: dict[str, Any] = {}
        for field in schema_properties:
            if field in field_errors:
                metadata_validation[field] = {
                    "valid": False,
                    "error": field_errors[field],
                }
            else:
                metadata_validation[field] = {"valid": True}

        # Also report errors for required fields that are missing (not in schema_properties
        # explicitly but listed as required).
        for field in required_fields:
            if field not in metadata_validation and field in field_errors:
                metadata_validation[field] = {
                    "valid": False,
                    "error": field_errors[field],
                }

        valid = len(field_errors) == 0

        return {
            "analyzer": self.name,
            "metadata": out_metadata,
            "metadata_validation": metadata_validation,
            "valid": valid,
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
