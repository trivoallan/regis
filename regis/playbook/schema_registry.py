"""Playbook schema registry — version → JSON Schema dispatch."""

from __future__ import annotations

import functools
import importlib.resources
import json
from collections.abc import Callable
from typing import Any


@functools.cache
def _load_schema_v1alpha1() -> dict[str, Any]:
    pkg = importlib.resources.files("regis.schemas.playbook.v1alpha1")
    text = pkg.joinpath("playbook.schema.json").read_text(encoding="utf-8")
    return json.loads(text)


_SCHEMAS: dict[str, Callable[[], dict[str, Any]]] = {
    "regis.trivoallan.dev/v1alpha1": _load_schema_v1alpha1,
}


def supported_versions() -> list[str]:
    """Return the sorted list of supported apiVersions."""
    return sorted(_SCHEMAS.keys())


def get_schema(api_version: str) -> dict[str, Any]:
    """Return the JSON Schema for *api_version*.

    Raises KeyError if the apiVersion is not supported.
    """
    try:
        loader = _SCHEMAS[api_version]
    except KeyError:
        raise KeyError(
            f"Unsupported apiVersion {api_version!r}. "
            f"Supported: {supported_versions()}."
        ) from None
    return loader()
