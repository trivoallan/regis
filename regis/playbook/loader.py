"""Playbook loading utilities.

Supports loading playbook definitions from:
- Local YAML or JSON files
- Local bundle directories (containing playbook.yaml)
- Remote HTTP/HTTPS URLs
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def load_playbook(path: str | Path) -> dict[str, Any]:
    """Load a playbook definition from a local file, bundle directory, or remote URL."""
    if isinstance(path, str) and (
        path.startswith("http://") or path.startswith("https://")
    ):
        import requests

        try:
            response = requests.get(path, timeout=30)
            response.raise_for_status()
            text = response.text
            # Infer format from URL or try YAML (which is a superset of JSON)
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
