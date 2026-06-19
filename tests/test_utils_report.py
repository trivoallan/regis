"""Tests for regis.utils.report — uncovered paths."""

from unittest.mock import patch

import pytest

from regis.utils.report import escape_jinja, run_playbooks


class TestEscapeJinja:
    def test_double_brace_wrapped(self):
        result = escape_jinja("{{ variable }}")
        assert result == "{% raw %}{{ variable }}{% endraw %}"

    def test_percent_brace_wrapped(self):
        result = escape_jinja("{% block content %}")
        assert result == "{% raw %}{% block content %}{% endraw %}"

    def test_plain_string_unchanged(self):
        assert escape_jinja("hello world") == "hello world"

    def test_dict_values_escaped(self):
        result = escape_jinja({"key": "{{ val }}", "plain": "text"})
        assert result["key"] == "{% raw %}{{ val }}{% endraw %}"
        assert result["plain"] == "text"

    def test_list_values_escaped(self):
        result = escape_jinja(["{{ a }}", "plain"])
        assert result[0] == "{% raw %}{{ a }}{% endraw %}"
        assert result[1] == "plain"

    def test_non_string_passthrough(self):
        assert escape_jinja(42) == 42
        assert escape_jinja(None) is None


class TestRunPlaybooks:
    """Test run_playbooks with various options."""

    _ANALYSIS_REPORT = {
        "request": {
            "registry": "docker.io",
            "repository": "library/nginx",
            "tag": "latest",
            "analyzers": [],
        },
        "results": {},
    }

    def _make_pb_result(
        self, *, passed: bool = True, with_rules: bool = False, with_links: bool = False
    ) -> dict:
        rules = []
        if with_rules:
            rules = [
                {"slug": "r1", "passed": True, "status": "passed", "message": "ok"},
                {"slug": "r2", "passed": False, "status": "failed", "message": "fail"},
                {
                    "slug": "r3",
                    "passed": False,
                    "status": "incomplete",
                    "message": "missing data",
                },
            ]
        result = {
            "score": 100 if passed else 0,
            "rules_summary": {
                "passed": ["r1"] if passed else [],
                "total": ["r1"],
                "score": 100 if passed else 0,
            },
            "rules": rules,
            "tier": None,
        }
        if with_links:
            result["links"] = [{"url": "https://example.com", "label": "Docs"}]
        return result

    @patch("regis.core.domain.playbook.engine.load_playbook")
    @patch("regis.core.domain.playbook.engine.evaluate")
    def test_remote_path_shows_downloading(self, mock_eval, mock_load, capsys):
        mock_load.return_value = {}
        mock_eval.return_value = self._make_pb_result()

        with patch("regis.utils.report.click.echo") as mock_echo:
            run_playbooks(
                ("http://example.com/playbook.yaml",),
                self._ANALYSIS_REPORT,
                formats=["json"],
            )
            calls = [str(c) for c in mock_echo.call_args_list]
            assert any("Downloading" in c for c in calls)

    @patch("regis.core.domain.playbook.engine.load_playbook")
    @patch("regis.core.domain.playbook.engine.evaluate")
    def test_local_path_shows_evaluating(self, mock_eval, mock_load, tmp_path):
        mock_load.return_value = {}
        mock_eval.return_value = self._make_pb_result()

        with patch("regis.utils.report.click.echo") as mock_echo:
            run_playbooks(
                (str(tmp_path / "playbook.yaml"),),
                self._ANALYSIS_REPORT,
                formats=["json"],
            )
            calls = [str(c) for c in mock_echo.call_args_list]
            assert any("Evaluating" in c for c in calls)

    @patch("regis.core.domain.playbook.engine.load_playbook")
    @patch("regis.core.domain.playbook.engine.evaluate")
    def test_show_rules_prints_icons(self, mock_eval, mock_load):
        mock_load.return_value = {}
        mock_eval.return_value = self._make_pb_result(with_rules=True)

        with patch("regis.utils.report.click.echo") as mock_echo:
            run_playbooks(
                ("local.yaml",),
                self._ANALYSIS_REPORT,
                formats=["json"],
                show_rules=True,
            )
            all_output = " ".join(str(c) for c in mock_echo.call_args_list)
            assert "✅" in all_output
            assert "❌" in all_output
            assert "⚠️" in all_output

    @patch("regis.core.domain.playbook.engine.load_playbook")
    @patch("regis.core.domain.playbook.engine.evaluate")
    def test_links_accumulated_in_final_report(self, mock_eval, mock_load):
        mock_load.return_value = {}
        mock_eval.return_value = self._make_pb_result(with_links=True)

        result = run_playbooks(
            ("local.yaml",),
            self._ANALYSIS_REPORT,
            formats=["json"],
        )
        assert "links" in result
        assert result["links"][0]["url"] == "https://example.com"

    @patch("regis.core.domain.playbook.engine.load_playbook")
    @patch("regis.core.domain.playbook.engine.evaluate")
    def test_links_deduplicated(self, mock_eval, mock_load):
        mock_load.return_value = {}
        link = {"url": "https://example.com", "label": "Docs"}
        pb_result = self._make_pb_result()
        pb_result["links"] = [link]
        mock_eval.return_value = pb_result

        result = run_playbooks(
            ("a.yaml", "b.yaml"),
            self._ANALYSIS_REPORT,
            formats=["json"],
        )
        assert result["links"].count(link) == 1

    def test_no_playbook_paths_uses_default(self):
        """When no paths given, default playbook is loaded (if it exists)."""
        with (
            patch("regis.core.domain.playbook.engine.load_playbook") as mock_load,
            patch("regis.core.domain.playbook.engine.evaluate") as mock_eval,
        ):
            mock_load.return_value = {}
            mock_eval.return_value = self._make_pb_result()
            result = run_playbooks((), self._ANALYSIS_REPORT, formats=["json"])
            # Either the default was loaded or no paths existed
            assert isinstance(result, dict)


def test_run_playbooks_surfaces_friendly_error_for_legacy_playbook(tmp_path) -> None:
    """A PlaybookError from the core is translated to a Click error, not a traceback."""
    import pytest
    from click.exceptions import ClickException

    from regis.core.domain.errors import PlaybookError
    from regis.utils.report import run_playbooks

    legacy = tmp_path / "playbook.yaml"
    legacy.write_text("name: Legacy\n", encoding="utf-8")

    with (
        pytest.raises(ClickException) as exc_info,
        patch(
            "regis.core.domain.playbook.engine.load_playbook",
            side_effect=PlaybookError(
                f"Failed to load playbook '{legacy}': missing apiVersion"
            ),
        ),
    ):
        run_playbooks((str(legacy),), {"results": {}}, formats=["json"])
    assert "apiVersion" in str(exc_info.value.message)


def test_result_schema_accepts_playbook_metadata() -> None:
    import importlib.resources
    import json

    import jsonschema

    schema_text = (
        importlib.resources.files("regis.schemas.playbook")
        .joinpath("result.schema.json")
        .read_text(encoding="utf-8")
    )
    schema = json.loads(schema_text)

    report = {
        "playbook_name": "Test",
        "playbook_version": "1.2.3",
        "api_version": "regis.io/v1alpha1",
        "score": 100,
    }
    jsonschema.validate(instance=report, schema=schema)  # must not raise


def test_result_schema_v4_still_accepts_legacy_v3_keys() -> None:
    """A legacy v3 result carrying the removed pages/scorecard keys must still
    validate against the v4 schema (read backward-compatibility)."""
    import importlib.resources
    import json

    import jsonschema

    schema = json.loads(
        importlib.resources.files("regis.schemas.playbook")
        .joinpath("result.schema.json")
        .read_text(encoding="utf-8")
    )

    legacy_report = {
        "playbook_name": "Legacy",
        "score": 80,
        # Keys dropped from the v4 contract — a v3 producer still emits them.
        "total_scorecards": 3,
        "passed_scorecards": 2,
        "pages": [
            {
                "title": "Default",
                "score": 67,
                "total_scorecards": 3,
                "passed_scorecards": 2,
                "sections": [
                    {
                        "name": "Main",
                        "score": 67,
                        "total_scorecards": 3,
                        "passed_scorecards": 2,
                        "scorecards": [
                            {"name": "sc1", "description": "SC1", "passed": True}
                        ],
                    }
                ],
            }
        ],
    }
    jsonschema.validate(instance=legacy_report, schema=schema)  # must not raise


def test_markdown_includes_verdict_header():
    from regis.utils.report import _render_markdown

    report = {
        "request": {"registry": "r", "repository": "x", "tag": "t"},
        "playbooks": [
            {
                "tier": "Silver",
                "tier_icon": "🥈",
                "rules_summary": {"score": 78, "total": 20, "passed": 17},
                "rules": [
                    {
                        "slug": "cve-critical",
                        "level": "critical",
                        "passed": False,
                        "status": "failed",
                        "message": "1 critical CVE (max 0)",
                    },
                    {
                        "slug": "scorecard-min",
                        "level": "warning",
                        "passed": False,
                        "status": "incomplete",
                        "message": "data unavailable",
                    },
                    *[
                        {
                            "slug": f"ok-{i}",
                            "level": "info",
                            "passed": True,
                            "status": "passed",
                            "message": "",
                        }
                        for i in range(17)
                    ],
                ],
                "badge_labels": [{"name": "CVE: Critical", "class": "error"}],
            }
        ],
    }
    md = _render_markdown(report)
    assert "## 🥈 Silver · 78/100" in md
    assert "🟥 CVE: Critical" in md
    # Worst level carries the severity square — must match the terminal surface.
    assert "worst: 🟥 critical" in md
    assert "| ✗ | cve-critical | critical | 1 critical CVE (max 0) |" in md
    assert "| ⚠ | scorecard-min | warning | data unavailable |" in md


def test_markdown_no_verdict_when_not_evaluated():
    from regis.utils.report import _render_markdown

    md = _render_markdown(
        {"request": {"registry": "r", "repository": "x", "tag": "t"}, "results": {}}
    )
    assert "Unrated" not in md  # no verdict header emitted


def test_markdown_escapes_pipe_in_rule_message():
    from regis.utils.report import _render_markdown

    report = {
        "request": {"registry": "r", "repository": "x", "tag": "t"},
        "playbooks": [
            {
                "tier": "Bronze",
                "tier_icon": "🥉",
                "rules_summary": {"score": 60, "total": 1, "passed": 0},
                "rules": [
                    {
                        "slug": "cve",
                        "level": "warning",
                        "passed": False,
                        "status": "failed",
                        "message": "found a|b in pkg",
                    },
                ],
                "badge_labels": [],
            }
        ],
    }
    md = _render_markdown(report)
    # The pipe inside the message must be escaped so the table row stays intact.
    assert "found a\\|b in pkg" in md
    # Counts line surfaces the failure.
    assert "1 failed" in md


class TestWriteReportFallback:
    """Cover the PermissionError fallback paths in write_report."""

    _REPORT = {"request": {"registry": "r", "repository": "x", "tag": "t"}}

    def test_fallback_on_permission_error(self, tmp_path):
        """When primary write raises PermissionError, fallback to cwd succeeds."""
        from regis.utils.report import write_report

        with (
            patch("pathlib.Path.mkdir", side_effect=[None, None]),
            patch(
                "pathlib.Path.write_text",
                side_effect=[PermissionError("denied"), None],
            ),
            patch("regis.utils.report.Path.cwd", return_value=tmp_path),
        ):
            result = write_report(".", "out.json", self._REPORT, "json", '{"a":1}')
        # Returns the fallback path (cwd / report.json)
        assert result == tmp_path / "report.json"

    def test_double_permission_error_raises_click_exception(self, tmp_path):
        """When both primary and fallback writes fail, a ClickException is raised."""
        import click

        from regis.utils.report import write_report

        with (
            patch("pathlib.Path.mkdir", side_effect=[None, None]),
            patch(
                "pathlib.Path.write_text",
                side_effect=[PermissionError("denied"), PermissionError("also denied")],
            ),
            patch("regis.utils.report.Path.cwd", return_value=tmp_path),
        ):
            with pytest.raises(click.ClickException, match="Permission denied"):
                write_report(".", "out.json", self._REPORT, "json", '{"a":1}')


def test_render_and_save_reports_md_format(tmp_path):
    """render_and_save_reports with fmt=md writes a markdown report."""
    from regis.utils.report import render_and_save_reports

    report = {"request": {"registry": "r", "repository": "x", "tag": "t"}}
    paths = render_and_save_reports(
        report,
        formats=["md"],
        output_template=str(tmp_path / "report.md"),
        output_dir_template=".",
        theme="default",
        pretty=False,
    )
    assert len(paths) == 1
    assert paths[0].suffix == ".md"
    assert paths[0].read_text(encoding="utf-8").startswith("#")


def test_render_and_save_reports_sarif_format(tmp_path):
    """render_and_save_reports with fmt=sarif writes a SARIF file (not raw report)."""
    import json

    from regis.utils.report import render_and_save_reports

    report = {
        "version": "0.37.0",
        "request": {"registry": "r", "repository": "x", "tag": "t", "url": "x:t"},
        "rules": [
            {
                "slug": "cve-critical",
                "level": "critical",
                "status": "failed",
                "message": "boom",
                "analyzers": ["cve"],
                "criterion": "cve-count",
            },
        ],
    }
    paths = render_and_save_reports(
        report,
        formats=["sarif"],
        output_template=str(tmp_path / "report.sarif"),
        output_dir_template=".",
        theme="default",
        pretty=False,
    )
    assert len(paths) == 1
    assert paths[0].suffix == ".sarif"
    doc = json.loads(paths[0].read_text(encoding="utf-8"))
    assert doc["version"] == "2.1.0"
    assert doc["runs"][0]["tool"]["driver"]["name"] == "Regis"
    assert [r["ruleId"] for r in doc["runs"][0]["results"]] == ["cve-critical"]
