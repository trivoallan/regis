"""Integration tests for --html flag in regis analyze and evaluate."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from regis.analyzers.base import BaseAnalyzer
from regis.commands.analyze import analyze, evaluate_cmd

_MINIMAL_REPORT = {
    "request": {
        "registry": "registry-1.docker.io",
        "repository": "library/nginx",
        "tag": "latest",
        "digest": "sha256-abc",
        "timestamp": "2026-04-25T10:00:00+00:00",
        "analyzers": [],
    },
    "results": {
        "trivy": {"score": 80, "vulnerabilities": []},
    },
    "playbooks": [],
}


class _DummyAnalyzer(BaseAnalyzer):
    """Minimal stub analyzer for tests."""

    name = "dummy"

    def analyze(self, client, repo, tag, platform=None):
        return {"analyzer": "dummy"}

    def validate(self, report):
        pass

    def default_rules(self):
        return []


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def _mock_analyze_infra(tmp_path):
    """Patch all infrastructure needed to run analyze without real analyzers."""
    dummy_client = MagicMock()
    dummy_client.get_digest.return_value = "sha256:abc"

    with (
        patch("regis.commands.analyze.RegistryClient", return_value=dummy_client),
        patch(
            "regis.commands.analyze._discover_analyzers",
            return_value={"dummy": _DummyAnalyzer},
        ),
        patch("regis.commands.analyze.run_playbooks", return_value=_MINIMAL_REPORT),
        patch("regis.commands.analyze.validate_report"),
        patch("regis.commands.analyze.render_mr_templates"),
        patch("regis.commands.analyze.render_and_save_reports") as mock_render,
    ):
        yield mock_render


def test_html_flag_adds_html_format(runner, tmp_path, _mock_analyze_infra):
    """--html passes 'html' in formats to render_and_save_reports."""
    result = runner.invoke(
        analyze,
        ["nginx:latest", "--html", "--output-dir", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    formats = _mock_analyze_infra.call_args[0][1]
    assert "html" in formats


def test_sections_forwarded_to_render(runner, tmp_path, _mock_analyze_infra):
    """--sections value is forwarded to render_and_save_reports as sections kwarg."""
    result = runner.invoke(
        analyze,
        [
            "nginx:latest",
            "--html",
            "--sections",
            "summary",
            "--output-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    call_kwargs = _mock_analyze_infra.call_args[1]
    assert call_kwargs.get("sections") == "summary"


def test_html_archive_mutually_exclusive(runner, tmp_path, _mock_analyze_infra):
    """--html and --archive together produce a UsageError."""
    result = runner.invoke(
        analyze,
        ["nginx:latest", "--html", "--archive", str(tmp_path)],
    )
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower()


def test_evaluate_cmd_html_flag(runner, tmp_path):
    """evaluate --html passes 'html' in formats."""
    report_file = tmp_path / "report.json"
    report_file.write_text(json.dumps(_MINIMAL_REPORT), encoding="utf-8")

    with (
        patch("regis.commands.analyze.run_playbooks", return_value=_MINIMAL_REPORT),
        patch("regis.commands.analyze.validate_report"),
        patch("regis.commands.analyze.render_mr_templates"),
        patch("regis.commands.analyze.render_and_save_reports") as mock_render,
    ):
        result = runner.invoke(
            evaluate_cmd,
            [str(report_file), "--html", "--output-dir", str(tmp_path)],
        )
        assert result.exit_code == 0, result.output
        formats = mock_render.call_args[0][1]
        assert "html" in formats


def test_evaluate_sections_forwarded_to_render(runner, tmp_path):
    """evaluate --sections value is forwarded to render_and_save_reports."""
    report_file = tmp_path / "report.json"
    report_file.write_text(json.dumps(_MINIMAL_REPORT), encoding="utf-8")

    with (
        patch("regis.commands.analyze.run_playbooks", return_value=_MINIMAL_REPORT),
        patch("regis.commands.analyze.validate_report"),
        patch("regis.commands.analyze.render_and_save_reports") as mock_render,
        patch("regis.commands.analyze.render_mr_templates"),
    ):
        result = runner.invoke(
            evaluate_cmd,
            [
                str(report_file),
                "--html",
                "--sections",
                "trivy",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.output
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("sections") == "trivy"


def test_render_and_save_html_writes_file(tmp_path):
    """render_and_save_reports with fmt=html writes report.html to disk."""
    from regis.utils.report import render_and_save_reports

    with patch("regis.report.html.render_html_single", return_value="<html>ok</html>"):
        # Plain strings without {format} placeholders: format_output_path returns them as-is.
        render_and_save_reports(
            _MINIMAL_REPORT,
            formats=["html"],
            output_template="report.html",
            output_dir_template=str(tmp_path),
            theme="default",
            pretty=True,
            sections="summary",
        )

    out = tmp_path / "report.html"
    assert out.exists()
    assert "<html>ok</html>" in out.read_text()


def test_html_not_in_formats_without_flag(runner, tmp_path, _mock_analyze_infra):
    """Without --html flag, 'html' is NOT in formats passed to render."""
    result = runner.invoke(
        analyze,
        ["nginx:latest", "--output-dir", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    formats = _mock_analyze_infra.call_args[0][1]
    assert "html" not in formats
