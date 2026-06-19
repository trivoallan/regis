"""AnalyzerProvider port — supplies the available analyzer classes to run."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping


class AnalyzerProvider(ABC):
    """Port: discovers/provides the analyzer classes to run.

    Returns analyzer *types* as bare ``type``, not ``type[BaseAnalyzer]``: this
    port lives in ``core.ports``, which may not import ``core.domain`` where
    ``BaseAnalyzer`` is defined (the layer rule forbids ports → domain). The
    concrete classes are supplied by a driven adapter
    (``EntryPointAnalyzerProvider``).
    """

    @abstractmethod
    def available(self) -> Mapping[str, type]:
        """Return a mapping of analyzer slug -> analyzer class."""
