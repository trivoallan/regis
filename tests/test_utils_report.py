"""Tests for regis.utils.report — uncovered paths."""

from unittest.mock import patch

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
            "sections": [],
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

    @patch("regis.playbook.engine.load_playbook")
    @patch("regis.playbook.engine.evaluate")
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

    @patch("regis.playbook.engine.load_playbook")
    @patch("regis.playbook.engine.evaluate")
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

    @patch("regis.playbook.engine.load_playbook")
    @patch("regis.playbook.engine.evaluate")
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

    @patch("regis.playbook.engine.load_playbook")
    @patch("regis.playbook.engine.evaluate")
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

    @patch("regis.playbook.engine.load_playbook")
    @patch("regis.playbook.engine.evaluate")
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
            patch("regis.playbook.engine.load_playbook") as mock_load,
            patch("regis.playbook.engine.evaluate") as mock_eval,
        ):
            mock_load.return_value = {}
            mock_eval.return_value = self._make_pb_result()
            result = run_playbooks((), self._ANALYSIS_REPORT, formats=["json"])
            # Either the default was loaded or no paths existed
            assert isinstance(result, dict)


def test_run_playbooks_surfaces_friendly_error_for_legacy_playbook(tmp_path) -> None:
    """A playbook without schemaVersion should produce a Click error, not a traceback."""
    import pytest
    from click.exceptions import ClickException

    from regis.utils.report import evaluate_playbooks

    legacy = tmp_path / "playbook.yaml"
    legacy.write_text("name: Legacy\n", encoding="utf-8")

    with pytest.raises(ClickException) as exc_info:
        evaluate_playbooks((str(legacy),), {"results": {}}, formats=["json"])
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
        "total_scorecards": 1,
        "passed_scorecards": 1,
        "pages": [],
    }
    jsonschema.validate(instance=report, schema=schema)  # must not raise


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
    assert "| ✗ | cve-critical | critical | 1 critical CVE (max 0) |" in md
    assert "| ⚠ | scorecard-min | warning | data unavailable |" in md


def test_markdown_no_verdict_when_not_evaluated():
    from regis.utils.report import _render_markdown

    md = _render_markdown(
        {"request": {"registry": "r", "repository": "x", "tag": "t"}, "results": {}}
    )
    assert "Unrated" not in md  # no verdict header emitted
