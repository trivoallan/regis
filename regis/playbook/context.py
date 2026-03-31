"""Data context utilities for the playbook evaluation engine.

Provides:
- ``_flatten``         — flatten a nested dict into dot-separated keys
- ``_build_context``   — build (raw_context, nested_context) from a report
- ``NamedList``        — list with slug/name-based access
- ``MissingDataTracker`` — dict that tracks missing-key accesses
"""

from __future__ import annotations

from typing import Any


def _flatten(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a nested dict into dot-separated keys.

    Example::

        {"results": {"tags": {"total_tags": 42}}}
        → {"results.tags.total_tags": 42}
    """
    flat: dict[str, Any] = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten(value, full_key))
        else:
            flat[full_key] = value
    return flat


def _build_context(report: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the two evaluation contexts from a report.

    Returns:
        (raw_context, nested_context) where raw_context is the flattened
        report merged with the original report, and nested_context is the
        original report (used for Jinja2 templates).
    """
    raw_context = _flatten(report)
    raw_context.update(report)
    return raw_context, report


class NamedList(list):
    """A list wrapper that allows item access by index, slug, or normalized name."""

    def __init__(self, data: list[Any]):
        super().__init__(data)
        self._keys: dict[str, Any] = {}
        for item in data:
            if isinstance(item, dict):
                if "slug" in item:
                    self._keys[item["slug"]] = item
                if "name" in item:
                    # Create a normalized name: lowercase, replace spaces/dashes with underscores
                    norm = item["name"].lower().replace(" ", "_").replace("-", "_")
                    self._keys[norm] = item

    def __getitem__(self, key: Any) -> Any:
        # Standard integer index access
        if isinstance(key, int):
            return super().__getitem__(key)

        # String-based access
        if isinstance(key, str):
            # Try interpreting as index first
            try:
                idx = int(key)
                return super().__getitem__(idx)
            except ValueError:
                pass

            # Lookup by slug or normalized name
            if key in self._keys:
                return self._keys[key]

        return super().__getitem__(key)


class MissingDataTracker(dict):
    """A dictionary wrapper that tracks which keys were accessed and if they were missing."""

    def __init__(
        self,
        data: dict[str, Any],
        path: str = "",
        root_tracker: MissingDataTracker | None = None,
    ):
        super().__init__(data)
        self.missing_accessed = False
        self.path = path
        self.accessed_keys: set[str]  # declared here; assigned in both branches below
        # If this is a nested tracker, use the root tracker's accessed_keys set
        if root_tracker:
            self.root = root_tracker
            self.accessed_keys = root_tracker.accessed_keys
        else:
            self.root = self
            self.accessed_keys = set()

    def __getitem__(self, key: str) -> Any:
        full_key = f"{self.path}.{key}" if self.path else key
        self.accessed_keys.add(full_key)
        try:
            val = super().__getitem__(key)
        except KeyError:
            self.root.missing_accessed = True
            raise

        if val is None:
            self.root.missing_accessed = True
            return None

        if isinstance(val, dict):
            return MissingDataTracker(val, full_key, self.root)
        return val

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key: object) -> bool:
        if isinstance(key, str):
            full_key = f"{self.path}.{key}" if self.path else key
            self.accessed_keys.add(full_key)
        if not super().__contains__(key):
            self.root.missing_accessed = True
            return False
        return True
