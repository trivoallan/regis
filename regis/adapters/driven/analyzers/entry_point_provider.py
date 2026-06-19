"""EntryPointAnalyzerProvider — AnalyzerProvider backed by entry-point discovery."""

from __future__ import annotations

from collections.abc import Mapping

from regis.core.domain.analyzers.discovery import discover_analyzers
from regis.core.ports.analyzer_provider import AnalyzerProvider


class EntryPointAnalyzerProvider(AnalyzerProvider):
    """Adapts ``regis.core.domain.analyzers`` entry-point discovery to the AnalyzerProvider port."""

    def available(self) -> Mapping[str, type]:
        return discover_analyzers()
