"""write_report and render_and_save_reports return the written paths."""

from regis.utils.report import render_and_save_reports, write_report

_REPORT = {
    "request": {
        "repository": "library/nginx",
        "tag": "1.27",
        "timestamp": "2026-06-14T10:00:00",
    }
}


def test_write_report_returns_written_path(tmp_path) -> None:
    path = write_report(
        dir_tmpl=str(tmp_path),
        file_tmpl="report.json",
        report=_REPORT,
        fmt="json",
        rendered='{"ok": true}',
    )
    assert path == (tmp_path / "report.json").resolve()
    assert path.read_text(encoding="utf-8") == '{"ok": true}'


def test_render_and_save_reports_returns_written_paths(tmp_path) -> None:
    paths = render_and_save_reports(
        _REPORT,
        ["json"],
        output_template=None,
        output_dir_template=str(tmp_path),
        theme="",
        pretty=True,
        sections="all",
    )
    assert paths == [(tmp_path / "report.json").resolve()]
    assert paths[0].exists()
