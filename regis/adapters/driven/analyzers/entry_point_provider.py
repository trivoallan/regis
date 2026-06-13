"""EntryPointAnalyzerProvider — AnalyzerProvider backed by entry-point discovery."""

from __future__ import annotations

from collections.abc import Mapping

from regis.analyzers.discovery import discover_analyzers
from regis.core.application.analyzer_provider import AnalyzerProvider


class EntryPointAnalyzerProvider(AnalyzerProvider):
    """Adapts ``regis.analyzers`` entry-point discovery to the AnalyzerProvider port."""

    def available(self) -> Mapping[str, type]:
        return discover_analyzers()
