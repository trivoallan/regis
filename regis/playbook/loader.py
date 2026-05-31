"""Playbook loading utilities.

Supports loading playbook definitions from:
- Local YAML or JSON files
- Local bundle directories (containing playbook.yaml)
- Remote HTTP/HTTPS URLs

Every playbook must declare ``schemaVersion`` (integer) at the top level.
The loader dispatches to the matching JSON Schema via the schema registry
and validates the playbook before returning.
"""

from __future__ import annotations

import importlib.resources
import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml
from referencing import Registry, Resource

from regis.playbook import schema_registry


class PlaybookVersionError(ValueError):
    """Raised when schemaVersion is missing, malformed, or unsupported."""


def load_playbook(path: str | Path) -> dict[str, Any]:
    """Load and validate a playbook from a file, bundle dir, or URL."""
    raw = _read_raw(path)
    schema_version = _extract_schema_version(raw, path)
    schema = _get_schema_or_raise(schema_version, path)
    _validate(raw, schema, path, schema_version)
    return raw


def _read_raw(path: str | Path) -> dict[str, Any]:
    if isinstance(path, str) and (
        path.startswith("http://") or path.startswith("https://")
    ):
        import requests

        try:
            response = requests.get(path, timeout=30)
            response.raise_for_status()
            text = response.text
            if path.lower().endswith(".json"):
                return json.loads(text)
            return yaml.safe_load(text)
        except Exception as exc:
            raise ValueError(f"Failed to download playbook from {path}: {exc}") from exc

    path = Path(path)
    if path.is_dir():
        path = path / "playbook.yaml"
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(text)


def _extract_schema_version(raw: dict[str, Any], path: str | Path) -> int:
    if "schemaVersion" not in raw:
        raise PlaybookVersionError(
            f"playbook '{path}' is missing required field 'schemaVersion'.\n"
            f"Add `schemaVersion: 1` at the top of the file.\n"
            f"Supported versions: {schema_registry.supported_versions()}."
        )
    value = raw["schemaVersion"]
    # YAML's `true`/`false` parse as bool (a subclass of int); reject explicitly.
    if isinstance(value, bool) or not isinstance(value, int):
        raise PlaybookVersionError(
            f"playbook '{path}' has an invalid schemaVersion: {value!r} must be an integer.\n"
            f"Supported versions: {schema_registry.supported_versions()}."
        )
    return value


def _get_schema_or_raise(schema_version: int, path: str | Path) -> dict[str, Any]:
    try:
        return schema_registry.get_schema(schema_version)
    except KeyError:
        from importlib.metadata import version as _pkg_version

        raise PlaybookVersionError(
            f"playbook '{path}' declares schemaVersion={schema_version} but this "
            f"regis (v{_pkg_version('regis')}) only supports "
            f"{schema_registry.supported_versions()}. "
            f"Upgrade regis or use a compatible playbook."
        ) from None


def _build_validator_registry(schema: dict[str, Any]) -> Registry:
    """Build a referencing.Registry that resolves the v1 schema's relative $refs."""
    pkg_root = importlib.resources.files("regis.schemas.playbook")
    jsonlogic_schema = json.loads(
        pkg_root.joinpath("jsonlogic.schema.json").read_text(encoding="utf-8")
    )
    return Registry().with_resources(
        [
            (schema.get("$id", ""), Resource.from_contents(schema)),
            (jsonlogic_schema.get("$id", ""), Resource.from_contents(jsonlogic_schema)),
            # v1 schema references jsonlogic.schema.json as "../jsonlogic.schema.json".
            # Provide both forms so the ref resolves regardless of base URI used by the validator.
            ("../jsonlogic.schema.json", Resource.from_contents(jsonlogic_schema)),
            ("jsonlogic.schema.json", Resource.from_contents(jsonlogic_schema)),
        ]
    )


def _validate(
    raw: dict[str, Any],
    schema: dict[str, Any],
    path: str | Path,
    schema_version: int,
) -> None:
    registry = _build_validator_registry(schema)
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    try:
        validator.validate(raw)
    except jsonschema.ValidationError as exc:
        exc.message = (
            f"playbook '{path}' failed validation against schemaVersion={schema_version}: "
            f"{exc.message}"
        )
        raise


def is_bundle(path: str | Path) -> bool:
    """Return True if *path* is a local directory (i.e. a playbook bundle)."""
    if isinstance(path, str) and (
        path.startswith("http://") or path.startswith("https://")
    ):
        return False
    return Path(path).is_dir()


def bundle_meta_schema_path(path: str | Path) -> Path | None:
    """Return the path to meta.schema.json inside a bundle, or None if absent."""
    schema = Path(path) / "meta.schema.json"
    return schema if schema.exists() else None
