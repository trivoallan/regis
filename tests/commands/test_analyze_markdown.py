"""Unit tests for --markdown flag and Markdown rendering in regis analyze."""

from click.testing import CliRunner

from regis.commands.analyze import analyze
from regis.utils.report import _render_markdown

# ---------------------------------------------------------------------------
# _render_markdown unit tests
# ---------------------------------------------------------------------------


def _minimal_report(**extra) -> dict:
    base: dict = {
        "request": {
            "registry": "registry-1.docker.io",
            "repository": "library/nginx",
            "tag": "latest",
            "timestamp": "2026-04-22T10:00:00+00:00",
        },
        "results": {},
        "playbooks": [],
    }
    base.update(extra)
    return base


def test_render_markdown_contains_header():
    md = _render_markdown(_minimal_report())
    assert "# " in md


def test_render_markdown_includes_snapshot_date():
    md = _render_markdown(_minimal_report(snapshot_date="2026-04-09"))
    assert "2026-04-09" in md


def test_render_markdown_omits_snapshot_date_when_empty():
    md = _render_markdown(_minimal_report(snapshot_date=""))
    assert "Snapshot date" not in md


def test_render_markdown_omits_snapshot_date_when_absent():
    md = _render_markdown(_minimal_report())
    assert "Snapshot date" not in md


def test_render_markdown_includes_playbook_table():
    report = _minimal_report(
        playbooks=[
            {
                "name": "default",
                "verdict": "pass",
                "rules": [
                    {"result": True},
                    {"result": False},
                ],
            }
        ]
    )
    md = _render_markdown(report)
    assert "default" in md
    assert "pass" in md
    assert "1" in md  # one failing rule


def test_render_markdown_includes_timestamp():
    md = _render_markdown(_minimal_report())
    assert "2026-04-22" in md


def test_render_markdown_no_snapshot_date_section_when_none():
    """Ensure the Snapshot date line is absent when the field is None."""
    report = _minimal_report()
    report["snapshot_date"] = None
    md = _render_markdown(report)
    assert "Snapshot date" not in md


# ---------------------------------------------------------------------------
# CLI --markdown flag: verify the option is registered
# ---------------------------------------------------------------------------


def test_analyze_help_contains_markdown_flag():
    runner = CliRunner()
    result = runner.invoke(analyze, ["--help"])
    assert result.exit_code == 0
    assert "--markdown" in result.output or "-m" in result.output
