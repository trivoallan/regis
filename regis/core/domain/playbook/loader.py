"""Playbook loading utilities.

Supports loading playbook definitions from:
- Local YAML or JSON files
- Local bundle directories (containing playbook.yaml)
- Remote HTTP/HTTPS URLs

Every playbook must declare ``apiVersion`` and ``kind: Playbook`` at the top level.
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

from regis.core.domain.playbook import schema_registry


class PlaybookVersionError(ValueError):
    """Raised when apiVersion is missing, malformed, or unsupported."""


def load_playbook(path: str | Path) -> dict[str, Any]:
    """Load and validate a playbook from a file, bundle dir, or URL."""
    raw = _read_raw(path)
    api_version = _extract_api_version(raw, path)
    schema = _get_schema_or_raise(api_version, path)
    _validate(raw, schema, path, api_version)
    return normalize_playbook(raw)


def normalize_playbook(raw: dict[str, Any]) -> dict[str, Any]:
    """Flatten the envelope into the internal shape consumers expect.

    Projects ``metadata``/``spec`` back onto the historical top-level keys
    (``name``, ``slug``, ``version``, ``description`` + ``spec.*``) so the
    evaluator, integrations and report code need no changes.

    Precondition: *raw* must be an already-validated envelope (apiVersion/kind present).
    """
    meta = raw.get("metadata", {})
    spec = raw.get("spec", {})
    labels = meta.get("labels", {})
    return {
        "apiVersion": raw["apiVersion"],
        "kind": raw["kind"],
        "metadata": meta,
        "spec": spec,
        "name": meta.get("title") or meta.get("name"),
        "slug": meta.get("name"),
        "version": labels.get("app.kubernetes.io/version"),
        "description": meta.get("description"),
        **spec,
    }


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


def _extract_api_version(raw: dict[str, Any], path: str | Path) -> str:
    if "apiVersion" not in raw:
        raise PlaybookVersionError(
            f"playbook '{path}' is missing required field 'apiVersion'.\n"
            f"Add `apiVersion: regis.io/v1alpha1` and `kind: Playbook` "
            f"at the top of the file (run `regis playbook upgrade` to migrate a "
            f"legacy playbook).\n"
            f"Supported: {schema_registry.supported_versions()}."
        )
    api_version = raw["apiVersion"]
    if not isinstance(api_version, str):
        raise PlaybookVersionError(
            f"playbook '{path}' has an invalid apiVersion: {api_version!r} "
            f"must be a string.\n"
            f"Supported: {schema_registry.supported_versions()}."
        )
    kind = raw.get("kind")
    if kind != "Playbook":
        raise PlaybookVersionError(
            f"playbook '{path}' has kind={kind!r}; expected 'Playbook'."
        )
    return api_version


def _get_schema_or_raise(api_version: str, path: str | Path) -> dict[str, Any]:
    try:
        return schema_registry.get_schema(api_version)
    except KeyError:
        from importlib.metadata import version as _pkg_version

        raise PlaybookVersionError(
            f"playbook '{path}' declares apiVersion={api_version!r} but this "
            f"regis (v{_pkg_version('regis')}) only supports "
            f"{schema_registry.supported_versions()}. "
            f"Upgrade regis or run `regis playbook upgrade`."
        ) from None


_registry_cache: dict[str, Registry] = {}


def _build_validator_registry(schema: dict[str, Any]) -> Registry:
    """Build a referencing.Registry that resolves the v1alpha1 schema's relative $refs.

    Results are memoized by schema ``$id`` so repeated calls (e.g. in bulk
    analysis or matrix CI) pay the file-read and Registry construction cost
    only once per distinct schema version.
    """
    schema_id = schema.get("$id", "")
    if schema_id not in _registry_cache:
        pkg_root = importlib.resources.files("regis.schemas.playbook")
        jsonlogic_schema = json.loads(
            pkg_root.joinpath("jsonlogic.schema.json").read_text(encoding="utf-8")
        )
        _registry_cache[schema_id] = Registry().with_resources(
            [
                (schema_id, Resource.from_contents(schema)),
                (
                    jsonlogic_schema.get("$id", ""),
                    Resource.from_contents(jsonlogic_schema),
                ),
                # v1 schema references jsonlogic.schema.json as "../jsonlogic.schema.json".
                # Provide both forms so the ref resolves regardless of base URI used by the validator.
                ("../jsonlogic.schema.json", Resource.from_contents(jsonlogic_schema)),
                ("jsonlogic.schema.json", Resource.from_contents(jsonlogic_schema)),
            ]
        )
    return _registry_cache[schema_id]


def _validate(
    raw: dict[str, Any],
    schema: dict[str, Any],
    path: str | Path,
    api_version: str,
) -> None:
    registry = _build_validator_registry(schema)
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    try:
        validator.validate(raw)
    except jsonschema.ValidationError as exc:
        exc.message = (
            f"playbook '{path}' failed validation against apiVersion={api_version}: "
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
