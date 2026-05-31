"""Playbook schema registry — version → JSON Schema dispatch."""

from __future__ import annotations

import functools
import importlib.resources
import json
from collections.abc import Callable
from typing import Any


@functools.cache
def _load_schema_v1() -> dict[str, Any]:
    pkg = importlib.resources.files("regis.schemas.playbook.v1")
    text = pkg.joinpath("definition.schema.json").read_text(encoding="utf-8")
    return json.loads(text)


_SCHEMAS: dict[int, Callable[[], dict[str, Any]]] = {
    1: _load_schema_v1,
}


def supported_versions() -> list[int]:
    """Return the sorted list of supported schema versions."""
    return sorted(_SCHEMAS.keys())


def get_schema(schema_version: int) -> dict[str, Any]:
    """Return the JSON Schema for *schema_version*.

    Raises KeyError if the version is not supported.
    """
    try:
        loader = _SCHEMAS[schema_version]
    except KeyError:
        raise KeyError(
            f"Unsupported schemaVersion {schema_version!r}. "
            f"Supported: {supported_versions()}."
        ) from None
    return loader()
