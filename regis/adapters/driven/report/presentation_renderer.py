"""CookiecutterPresentationRenderer — PresentationRenderer backed by the util."""

from __future__ import annotations

from regis.core.model.report import Report
from regis.core.ports.presentation_renderer import PresentationRenderer
from regis.utils.report import render_presentation_templates


class CookiecutterPresentationRenderer(PresentationRenderer):
    """Renders presentation templates via the cookiecutter-backed util.

    Constructor-configured with the output-dir template (mirrors FileReportSink);
    ``render`` delegates to ``regis.utils.report.render_presentation_templates``.
    """

    def __init__(self, *, output_dir_template: str) -> None:
        self._output_dir_template = output_dir_template

    def render(self, report: Report) -> None:
        render_presentation_templates(report.payload, self._output_dir_template)
