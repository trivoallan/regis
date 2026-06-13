"""AnalyzerProvider port — supplies the available analyzers to the application."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping


class AnalyzerProvider(ABC):
    """Application-facing port: discovers/provides the analyzer classes to run.

    Returns analyzer *types*. The concrete bound (``type[BaseAnalyzer]``) is
    deferred to P4 when analyzers move into ``regis.core.domain``; typed as
    ``type`` here so the core stays free of legacy ``regis.analyzers`` imports.
    """

    @abstractmethod
    def available(self) -> Mapping[str, type]:
        """Return a mapping of analyzer slug -> analyzer class."""
