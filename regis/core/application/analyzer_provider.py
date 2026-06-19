"""AnalyzerProvider port — supplies the available analyzers to the application."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping


class AnalyzerProvider(ABC):
    """Application-facing port: discovers/provides the analyzer classes to run.

    Returns analyzer *types*, typed as bare ``type`` rather than
    ``type[BaseAnalyzer]``. Now that analyzers live in
    ``regis.core.domain.analyzers``, binding the concrete class is layer-legal
    from here (application may import domain) — but it would block the mooted
    move of this provider into ``core.ports`` (ports may not import domain).
    Left as ``type`` pending that decision.
    """

    @abstractmethod
    def available(self) -> Mapping[str, type]:
        """Return a mapping of analyzer slug -> analyzer class."""
