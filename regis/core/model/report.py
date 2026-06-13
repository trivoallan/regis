"""Report value object — a thin wrapper over the analysis report envelope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Report:
    """Wraps the report envelope payload (the JSON-Schema-validated dict).

    Intentionally thin in P1: the dict payload remains the source of truth.
    Rich field-level modeling is deferred to a later phase.
    """

    payload: dict[str, Any]

    @property
    def schema_version(self) -> int | None:
        """The integer envelope schema version, or None if absent/non-integer."""
        value = self.payload.get("schemaVersion")
        return value if isinstance(value, int) else None
