"""Report value object — a thin wrapper over the analysis report envelope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

REPORT_SCHEMA_VERSION = 5
"""Current report-structure contract version (see report.schema.json).

v5 removed the ``snapshot_date`` field (an editorial doc-site marker, not a
data-freshness indicator).  v4 removed the legacy
``pages``/``sections``/``scorecards``/``widgets`` rendering subsystem (and the
per-section ``levels_summary``/``tags_summary``); playbook results are now
rules-based only.
"""


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
