"""EntryPointAnalyzerProvider delegates to discover_analyzers."""

from regis.adapters.driven.analyzers import entry_point_provider
from regis.adapters.driven.analyzers.entry_point_provider import (
    EntryPointAnalyzerProvider,
)
from regis.core.ports.analyzer_provider import AnalyzerProvider


def test_is_an_analyzer_provider() -> None:
    assert isinstance(EntryPointAnalyzerProvider(), AnalyzerProvider)


def test_available_delegates_to_discovery(monkeypatch) -> None:
    stub = {"cve": object, "sbom": object}
    monkeypatch.setattr(entry_point_provider, "discover_analyzers", lambda: stub)
    assert EntryPointAnalyzerProvider().available() == stub
