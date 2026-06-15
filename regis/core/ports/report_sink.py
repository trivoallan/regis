"""ReportSink port — emission of analysis reports."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path

from regis.core.model.report import Report


class ReportSink(ABC):
    """Port for emitting a report in one or more formats to a destination."""

    @abstractmethod
    def emit(self, report: Report, *, formats: Sequence[str]) -> list[Path]:
        """Emit *report* in *formats* to this sink's configured destination; return the written paths."""
