"""FileReportSink — ReportSink that writes report files to disk."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from regis.core.model.report import Report
from regis.core.ports.report_sink import ReportSink
from regis.utils.report import render_and_save_reports


class FileReportSink(ReportSink):
    """Writes the report in the requested formats to a configured destination.

    Wraps the legacy emission in ``regis.utils.report``. Cookiecutter presentation
    templates are a separate concern (P4).
    """

    def __init__(
        self,
        *,
        output_dir_template: str,
        output_template: str | None = None,
        theme: str = "default",
        pretty: bool = True,
        sections: str = "all",
    ) -> None:
        self._output_dir_template = output_dir_template
        self._output_template = output_template
        self._theme = theme
        self._pretty = pretty
        self._sections = sections

    def emit(self, report: Report, *, formats: Sequence[str]) -> list[Path]:
        return render_and_save_reports(
            report.payload,
            list(formats),
            self._output_template,
            self._output_dir_template,
            self._theme,
            self._pretty,
            sections=self._sections,
        )
