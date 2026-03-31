"""Analyzer discovery via entry_points."""

from __future__ import annotations

import logging
from importlib.metadata import entry_points

from regis.analyzers.base import BaseAnalyzer

logger = logging.getLogger(__name__)


def discover_analyzers() -> dict[str, type[BaseAnalyzer]]:
    """Discover all registered analyzers via entry_points."""
    eps = entry_points(group="regis.analyzers")
    discovered: dict[str, type[BaseAnalyzer]] = {}
    for ep in eps:
        try:
            cls = ep.load()
            discovered[ep.name] = cls
        except Exception:
            logger.warning("Failed to load analyzer '%s'", ep.name, exc_info=True)
    return discovered
