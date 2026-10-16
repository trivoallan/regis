"""Unit tests for --markdown flag and Markdown rendering in regis analyze."""

from click.testing import CliRunner

from regis.adapters.driving.cli.commands.analyze import analyze
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


def test_markdown_playbook_results_reads_engine_keys():
    """The table reads the keys the playbook engine writes, not legacy ones."""
    report = {
        "request": {"registry": "r", "repository": "x", "tag": "t"},
        "playbooks": [
            {
                "playbook_name": "base-images",
                "tier": "Transformation requise",
                "tier_icon": "🔧",
                "score": 56,
                "rules": [
                    {"slug": "a", "passed": False, "status": "failed"},
                    {"slug": "b", "passed": False, "status": "failed"},
                    {"slug": "c", "passed": False, "status": "incomplete"},
                    {"slug": "d", "passed": True, "status": "passed"},
                ],
            }
        ],
    }
    md = _render_markdown(report)
    assert "| base-images | 🔧 Transformation requise · 56/100 | 2 |" in md


def test_render_markdown_includes_timestamp():
    md = _render_markdown(_minimal_report())
    assert "2026-04-22" in md


# ---------------------------------------------------------------------------
# CLI --markdown flag: verify the option is registered
# ---------------------------------------------------------------------------


def test_analyze_help_contains_markdown_flag():
    runner = CliRunner()
    result = runner.invoke(analyze, ["--help"])
    assert result.exit_code == 0
    assert "--markdown" in result.output or "-m" in result.output
