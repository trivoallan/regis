"""FileReportSink writes report files and returns their paths."""

from pathlib import Path

from regis.adapters.driven.report import file_report_sink as mod
from regis.adapters.driven.report.file_report_sink import FileReportSink
from regis.core.model.report import Report
from regis.core.ports.report_sink import ReportSink

_REPORT = Report(
    payload={
        "request": {
            "repository": "library/nginx",
            "tag": "1.27",
            "timestamp": "2026-06-14T10:00:00",
        }
    }
)


def test_is_a_report_sink() -> None:
    assert isinstance(FileReportSink(), ReportSink)


def test_emit_writes_json_and_returns_path(tmp_path) -> None:
    paths = FileReportSink().emit(_REPORT, formats=["json"], output_dir=tmp_path)
    assert paths == [(tmp_path / "report.json").resolve()]
    assert paths[0].exists()


def test_emit_delegates_with_port_args(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_render(
        report, formats, output_template, output_dir_template, theme, pretty, sections
    ):
        captured.update(
            report=report,
            formats=formats,
            output_template=output_template,
            output_dir_template=output_dir_template,
            theme=theme,
            pretty=pretty,
            sections=sections,
        )
        return [Path("/out/report.json")]

    monkeypatch.setattr(mod, "render_and_save_reports", fake_render)
    result = FileReportSink().emit(
        _REPORT, formats=["json", "md"], output_dir=Path("/out")
    )
    assert result == [Path("/out/report.json")]
    assert captured["report"] == _REPORT.payload
    assert captured["formats"] == ["json", "md"]
    assert captured["output_template"] is None
    assert captured["output_dir_template"] == "/out"
    assert captured["sections"] == "all"
    assert captured["pretty"] is True
