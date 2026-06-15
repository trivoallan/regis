"""Evaluate — application use-case for the dry-run ``regis evaluate`` path.

Re-runs playbook evaluation against an *existing* analysis report (no analyzer
loop, no envelope assembly, no breach/verdict), validates the result, and emits
it through the :class:`~regis.core.ports.report_sink.ReportSink` port.

Layering: this module imports ``regis.core.*`` only and never imports ``click``.
The CLI adapter loads the input file and translates ``PlaybookError`` into
``click.ClickException`` at the process boundary.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from regis.core.application.playbook_runner import run_playbooks, validate_report
from regis.core.model.report import Report
from regis.core.ports.report_sink import ReportSink


class Evaluate:
    """Evaluate playbooks against an existing report and emit the result."""

    def __init__(self, *, sink: ReportSink) -> None:
        self._sink = sink

    def run(
        self,
        report: dict[str, Any],
        *,
        formats: list[str],
        playbook_paths: tuple[str, ...] = (),
        on_playbook_progress: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """Run playbooks against ``report``, validate, emit; return the final report.

        Args:
            report: An existing analysis report (must already contain ``results``).
            formats: Output formats to emit (e.g. ``["json"]``).
            playbook_paths: Paths to playbook files/dirs; uses the built-in default
                when empty.
            on_playbook_progress: Optional callback invoked with progress messages
                during playbook evaluation.

        Returns:
            The final report dict (with ``playbooks`` populated).

        Raises:
            PlaybookError: When report schema validation fails.
        """
        final_report = run_playbooks(
            playbook_paths, report, on_progress=on_playbook_progress
        )
        validate_report(final_report)
        self._sink.emit(Report(final_report), formats=formats)
        return final_report
