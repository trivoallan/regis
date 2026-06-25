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
from datetime import datetime, timezone
from typing import Any

from regis.core.application.playbook_runner import run_playbooks, validate_report
from regis.core.domain.context import AnalysisContext
from regis.core.domain.errors import AnalyzerError, RegistryError, ToolError
from regis.core.domain.rules.breach import breached_slugs
from regis.core.model.image_reference import ImageReference
from regis.core.model.report import REPORT_SCHEMA_VERSION, Report
from regis.core.ports.image_inspector import ImageInspector
from regis.core.ports.presentation_renderer import PresentationRenderer
from regis.core.ports.report_sink import ReportSink
from regis.core.ports.tool_runner import ToolRunner

logger = logging.getLogger(__name__)

#: Factory producing a per-image ImageInspector (regctl-backed in production).
InspectorFactory = Callable[[ImageReference], ImageInspector]

#: Decorator that wraps the run-scoped ToolRunner (e.g. CachingToolRunner).
#: Supplied by the composition root; takes (base_tools, share) -> ToolRunner.
ToolsDecorator = Callable[[ToolRunner, bool], ToolRunner]

#: Analyzer names whose tools (grype, syft) read the image; sharing the one
#: local OCI pull is only worth it when BOTH run.
_CVE_ANALYZER = "cve"
_SBOM_ANALYZER = "sbom"


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


@dataclass(frozen=True)
class AnalysisResult:
    """Outcome of a full analyze-and-evaluate run."""

    report: dict[str, Any]
    has_breaches: bool
    breach_count: int
    breached_slugs: list[str]


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
        sink: ReportSink,
        presentation: PresentationRenderer,
        tools_decorator: ToolsDecorator | None = None,
    ) -> None:
        self._tools = tools
        self._inspector_factory = inspector_factory
        self._sink = sink
        self._presentation = presentation
        self._tools_decorator = tools_decorator

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def _dispatch(
        self,
        analyzer: Any,
        image: ImageReference,
        inspector: ImageInspector,
        tools: ToolRunner,
    ) -> dict[str, Any]:
        """Run one analyzer instance against a shared inspector + tools; validate."""
        ctx = AnalysisContext(image, inspector, tools)
        report = analyzer.analyze(ctx)
        analyzer.validate(report)
        return report

    def run_one(self, image: ImageReference, analyzer_cls: type) -> dict[str, Any]:
        """Run a single analyzer class and return its report (re-raises on error).

        The ``tools_decorator`` is intentionally NOT applied here: a single
        analyzer has nothing to share a layout with, so it scans the remote ref
        directly via ``self._tools``.
        """
        analyzer = analyzer_cls()
        inspector = self._inspector_factory(image)
        start = time.monotonic()
        try:
            return self._dispatch(analyzer, image, inspector, self._tools)
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
        inspector = self._inspector_factory(image)
        share = _CVE_ANALYZER in selected and _SBOM_ANALYZER in selected
        tools = (
            self._tools_decorator(self._tools, share)
            if self._tools_decorator is not None
            else self._tools
        )

        def _timed(name: str, cls: type) -> tuple[str, dict[str, Any]]:
            # Record the start time before instantiation so a constructor that
            # raises is still timed and the draining thread reads a real elapsed.
            start_times[name] = time.monotonic()
            try:
                return name, self._dispatch(cls(), image, inspector, tools)
            finally:
                logger.debug(
                    "analyzer %s finished in %.2fs",
                    name,
                    time.monotonic() - start_times[name],
                )

        workers = min(max_workers, len(selected)) or 1
        try:
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
        finally:
            # The ThreadPoolExecutor 'with' block joins before this runs, so no
            # worker is still reading a layout when it is removed. Duck-typed on
            # purpose: only a run-scoped decorator (CachingToolRunner) is
            # closeable, and we keep `close` off the ToolRunner port rather than
            # add a Closeable protocol for this single call site.
            close = getattr(tools, "close", None)
            if callable(close):
                close()
        return reports

    # ------------------------------------------------------------------
    # Full pipeline: analyze + playbooks + emit
    # ------------------------------------------------------------------

    def run_and_evaluate(
        self,
        image: ImageReference,
        selected: Mapping[str, type],
        *,
        url: str,
        digest: str,
        formats: list[str],
        metadata: dict[str, Any] | None = None,
        playbook_paths: tuple[str, ...] = (),
        show_rules: bool = False,
        on_playbook_progress: Callable[[str], None] | None = None,
        fail_level: str = "critical",
        max_workers: int = 4,
        on_progress: ProgressCallback | None = None,
    ) -> AnalysisResult:
        """Run analyzers, assemble the envelope, evaluate playbooks, validate, emit.

        Args:
            image: The image reference to analyze.
            selected: Mapping of analyzer name to class.
            url: The image URL string (for the request envelope).
            digest: The resolved image digest.
            formats: Output formats to emit (e.g. ``["json"]``).
            metadata: Optional arbitrary metadata to embed in the report envelope.
            playbook_paths: Paths to playbook files/dirs; uses built-in default when
                empty.
            show_rules: When ``True``, progress messages include per-rule icons.
            on_playbook_progress: Optional callback invoked with progress messages
                during playbook evaluation.
            fail_level: Severity threshold for breach detection
                (``"critical"`` | ``"warning"`` | ``"info"`` | ``"none"``).
            max_workers: Maximum threads for the analyzer loop.
            on_progress: Optional callback invoked once per analyzer completion.

        Returns:
            An :class:`AnalysisResult` with the final report and breach summary.

        Raises:
            AnalyzerError: When ``selected`` is empty (no analyzers to run).
            PlaybookError: When report schema validation fails.
        """
        from importlib.metadata import version as _pkg_version

        reports = self.run(
            image, selected, max_workers=max_workers, on_progress=on_progress
        )
        if not reports:
            raise AnalyzerError("All analyzers failed.")

        envelope: dict[str, Any] = {
            "schemaVersion": REPORT_SCHEMA_VERSION,
            "version": _pkg_version("regis"),
            "request": {
                "url": url,
                "registry": image.registry,
                "repository": image.repository,
                "tag": image.tag,
                "digest": digest,
                "analyzers": sorted(reports.keys()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "results": reports,
        }
        if metadata:
            envelope["metadata"] = metadata

        final_report = run_playbooks(
            playbook_paths,
            envelope,
            show_rules=show_rules,
            on_progress=on_playbook_progress,
        )
        if show_rules and final_report.get("playbooks"):
            pb0 = final_report["playbooks"][0]
            final_report["rules"] = pb0.get("rules", [])
            final_report["rules_summary"] = pb0.get("rules_summary", {})
            final_report["tier"] = pb0.get("tier")
            final_report["badges"] = pb0.get("badges", [])

        validate_report(final_report)
        self._sink.emit(Report(final_report), formats=formats)
        self._presentation.render(Report(final_report))

        breached = breached_slugs(final_report.get("rules", []), fail_level)
        return AnalysisResult(final_report, bool(breached), len(breached), breached)
