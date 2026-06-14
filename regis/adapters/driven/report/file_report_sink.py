"""FileReportSink — ReportSink that writes report files to disk."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from regis.core.model.report import Report
from regis.core.ports.report_sink import ReportSink
from regis.utils.report import render_and_save_reports


class FileReportSink(ReportSink):
    """Writes the report in the requested formats under *output_dir*.

    Wraps the legacy emission in ``regis.utils.report``. The cookiecutter
    presentation-template rendering is a separate concern, handled elsewhere
    (P3/P4). Not yet consumed by the CLI — wiring is P3.
    """

    def emit(
        self, report: Report, *, formats: Sequence[str], output_dir: Path
    ) -> list[Path]:
        return render_and_save_reports(
            report.payload,
            list(formats),
            output_template=None,
            output_dir_template=str(output_dir),
            theme="",
            pretty=True,
            sections="all",
        )
