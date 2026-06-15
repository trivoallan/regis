"""AnalyzeImage — application use-case running the analyzer loop.

Owns *only* the analyzer loop: it builds a ThreadPoolExecutor, dispatches each
analyzer via the hexagonal ``analyze(ctx)`` contract, validates each report,
captures errors into stubs, and reports progress.

Layering: this module imports ``regis.core.*`` only. The ``RegistryClient``
and the regctl ``ImageInspector`` are supplied as **injected callables** by the
CLI composition root, so the core references no adapter type.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

from regis.core.domain.context import AnalysisContext
from regis.core.domain.errors import AnalyzerError, RegistryError, ToolError
from regis.core.model.image_reference import ImageReference
from regis.core.ports.image_inspector import ImageInspector
from regis.core.ports.tool_runner import ToolRunner

logger = logging.getLogger(__name__)

#: Factory producing a per-image ImageInspector (regctl-backed in production).
InspectorFactory = Callable[[ImageReference], ImageInspector]


@dataclass(frozen=True)
class AnalyzerOutcome:
    """One analyzer's result, reported to the ``on_progress`` callback.

    ``error_type`` is ``None`` on success; otherwise one of
    ``"registry" | "analysis" | "tool" | "unexpected"``.
    """

    name: str
    elapsed: float
    error_type: str | None = None
    error_message: str | None = None


ProgressCallback = Callable[[AnalyzerOutcome], None]

# Maps a caught exception to (error stub "type", AnalyzerOutcome error_type).
_ERROR_KIND: tuple[tuple[type[BaseException], str], ...] = (
    (RegistryError, "registry"),
    (AnalyzerError, "analysis"),
    (ToolError, "tool"),
)


def _classify(exc: BaseException) -> str:
    for exc_type, kind in _ERROR_KIND:
        if isinstance(exc, exc_type):
            return kind
    return "unexpected"


class AnalyzeImage:
    """Run the selected analyzers against an image and collect their reports."""

    def __init__(
        self,
        *,
        tools: ToolRunner,
        inspector_factory: InspectorFactory,
    ) -> None:
        self._tools = tools
        self._inspector_factory = inspector_factory

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, analyzer: Any, image: ImageReference) -> dict[str, Any]:
        """Run one analyzer instance and validate its report."""
        ctx = AnalysisContext(image, self._inspector_factory(image), self._tools)
        report = analyzer.analyze(ctx)
        analyzer.validate(report)
        return report

    def run_one(self, image: ImageReference, analyzer_cls: type) -> dict[str, Any]:
        """Run a single analyzer class and return its report (re-raises on error)."""
        analyzer = analyzer_cls()
        start = time.monotonic()
        try:
            return self._dispatch(analyzer, image)
        finally:
            logger.debug(
                "analyzer %s finished in %.2fs",
                getattr(analyzer, "name", analyzer_cls.__name__),
                time.monotonic() - start,
            )

    # ------------------------------------------------------------------
    # Parallel loop
    # ------------------------------------------------------------------

    def run(
        self,
        image: ImageReference,
        selected: Mapping[str, type],
        *,
        max_workers: int = 4,
        on_progress: ProgressCallback | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Run ``selected`` analyzers in parallel; return {name: report-or-stub}.

        Failures are captured as ``{"analyzer": name, "error": {...}}`` stubs so a
        single analyzer cannot abort the run. ``on_progress`` (if given) is called
        once per analyzer **from the draining thread** (not the workers), so a
        click-based callback prints without interleaving.
        """
        reports: dict[str, Any] = {}
        if not selected:
            return reports
        start_times: dict[str, float] = {}

        def _timed(name: str, cls: type) -> tuple[str, dict[str, Any]]:
            # Record the start time before instantiation so a constructor that
            # raises is still timed and the draining thread reads a real elapsed.
            start_times[name] = time.monotonic()
            try:
                return name, self._dispatch(cls(), image)
            finally:
                logger.debug(
                    "analyzer %s finished in %.2fs",
                    name,
                    time.monotonic() - start_times[name],
                )

        workers = min(max_workers, len(selected)) or 1
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_timed, name, cls): name
                for name, cls in selected.items()
            }
            for future in as_completed(futures):
                name = futures[future]
                elapsed = time.monotonic() - start_times.get(name, time.monotonic())
                try:
                    _, report = future.result()
                    reports[name] = report
                    if on_progress is not None:
                        on_progress(AnalyzerOutcome(name, elapsed))
                # Capture and classify any analyzer failure; never abort the run.
                except Exception as exc:  # noqa: BLE001
                    kind = _classify(exc)
                    reports[name] = {
                        "analyzer": name,
                        "error": {"type": kind, "message": str(exc)},
                    }
                    if on_progress is not None:
                        on_progress(AnalyzerOutcome(name, elapsed, kind, str(exc)))
        return reports
