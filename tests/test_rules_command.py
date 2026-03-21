"""Tests for 'regis-cli rules show' and 'rules evaluate' commands."""

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from regis_cli.cli import main

# Minimal analysis report that satisfies the evaluator
_MINIMAL_REPORT = {
    "request": {
        "registry": "docker.io",
        "repository": "library/nginx",
        "tag": "latest",
        "analyzers": [],
    },
    "results": {},
}


class TestRulesShow:
    def test_show_existing_rule(self):
        runner = CliRunner()
        result = runner.invoke(main, ["rules", "show", "registry-domain-whitelist"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["slug"] == "registry-domain-whitelist"
        assert data["level"] == "critical"

    def test_show_unknown_rule_fails(self):
        runner = CliRunner()
        result = runner.invoke(main, ["rules", "show", "nonexistent-slug"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_show_with_nonexistent_rules_file(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "rules",
                "show",
                "registry-domain-whitelist",
                "--rules",
                str(tmp_path / "missing.yaml"),
            ],
        )
        # Should still work — missing file is silently ignored
        assert result.exit_code == 0


class TestRulesList:
    def test_markdown_with_params_shows_options(self):
        """rules list --format markdown renders params for rules that have them."""
        runner = CliRunner()
        result = runner.invoke(main, ["rules", "list", "--format", "markdown"])
        assert result.exit_code == 0
        # registry-domain-whitelist has params.domains
        assert "domains" in result.output

    def test_nonexistent_rules_file_ignored(self, tmp_path):
        """Passing a non-existent --rules file should not crash."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["rules", "list", "--rules", str(tmp_path / "ghost.yaml")],
        )
        assert result.exit_code == 0
        # Default rules still shown
        assert "registry-domain-whitelist" in result.output


class TestRulesEvaluate:
    def _write_report(self, tmp_path: Path, report: dict | None = None) -> Path:
        p = tmp_path / "report.json"
        p.write_text(json.dumps(report or _MINIMAL_REPORT), encoding="utf-8")
        return p

    def test_stdout_output(self, tmp_path):
        report_file = self._write_report(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["rules", "evaluate", str(report_file)])
        assert result.exit_code == 0
        assert "Rules Evaluation Score" in result.output

    def test_file_output(self, tmp_path):
        report_file = self._write_report(tmp_path)
        out_file = tmp_path / "eval.json"
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["rules", "evaluate", str(report_file), "-o", str(out_file)],
        )
        assert result.exit_code == 0
        assert out_file.exists()
        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert "score" in data
        assert "rules" in data

    def test_with_rules_yaml(self, tmp_path):
        report_file = self._write_report(tmp_path)
        rules_yaml = tmp_path / "rules.yaml"
        rules_yaml.write_text("rules: []\n", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["rules", "evaluate", str(report_file), "--rules", str(rules_yaml)],
        )
        assert result.exit_code == 0

    def test_invalid_report_json_fails(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not json", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, ["rules", "evaluate", str(bad)])
        assert result.exit_code != 0
        assert "Failed to load report file" in result.output

    def test_invalid_rules_yaml_fails(self, tmp_path):
        report_file = self._write_report(tmp_path)
        bad_rules = tmp_path / "bad.yaml"
        bad_rules.write_text(":\ninvalid:\n  - yaml: [unclosed", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["rules", "evaluate", str(report_file), "--rules", str(bad_rules)],
        )
        assert result.exit_code != 0
        assert "Failed to load rules file" in result.output

    def test_fail_flag_exits_nonzero_on_breach(self, tmp_path):
        """--fail exits 1 when a failing rule meets the fail-level threshold."""
        report_file = self._write_report(
            tmp_path,
            {
                **_MINIMAL_REPORT,
                "request": {
                    **_MINIMAL_REPORT["request"],
                    "registry": "unknown.registry.io",
                },
            },
        )
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "rules",
                "evaluate",
                str(report_file),
                "--fail",
                "--fail-level",
                "critical",
            ],
        )
        assert result.exit_code != 0

    def test_fail_flag_exits_zero_no_breach(self, tmp_path):
        """--fail exits 0 when the failing rule is below the fail-level threshold."""
        # Use docker.io which passes the whitelist check
        report_file = self._write_report(tmp_path)
        runner = CliRunner()
        with patch("regis_cli.rules.evaluator.evaluate_rules") as mock_eval:
            mock_eval.return_value = {
                "score": 100,
                "all_rules": ["r1"],
                "passed_rules": ["r1"],
                "by_tag": {},
                "rules": [
                    {
                        "slug": "r1",
                        "passed": True,
                        "level": "info",
                        "status": "passed",
                        "message": "",
                    }
                ],
            }
            result = runner.invoke(
                main,
                [
                    "rules",
                    "evaluate",
                    str(report_file),
                    "--fail",
                    "--fail-level",
                    "critical",
                ],
            )
        assert result.exit_code == 0
