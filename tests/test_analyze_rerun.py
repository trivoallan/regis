"""Tests for the --rerun and --report flags of the analyze command."""

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from regis.analyzers.metadata import MetadataAnalyzer
from regis.cli import main


class TestRerunReportFlagValidation:
    """Mutual dependency validation between --rerun and --report."""

    def test_rerun_requires_report(self):
        runner = CliRunner()
        result = runner.invoke(main, ["analyze", "--rerun", "metadata"])
        assert result.exit_code != 0
        assert "requires --report" in result.output

    def test_report_requires_rerun(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("report_dir").mkdir()
            result = runner.invoke(main, ["analyze", "--report", "report_dir"])
        assert result.exit_code != 0
        assert "requires --rerun" in result.output

    def test_no_url_without_rerun(self):
        runner = CliRunner()
        result = runner.invoke(main, ["analyze"])
        assert result.exit_code != 0


class TestRerunUnknownAnalyzer:
    """Error handling for unrecognised analyzer names."""

    @patch("regis.commands.analyze._discover_analyzers")
    def test_rerun_unknown_analyzer(self, mock_discover):
        mock_discover.return_value = {"metadata": MetadataAnalyzer}

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("report_dir").mkdir()
            result = runner.invoke(
                main,
                ["analyze", "--rerun", "nonexistent", "--report", "report_dir"],
            )

        assert result.exit_code != 0
        assert "Unknown analyzer" in result.output


class TestRerunReportNotFound:
    """Error when the report directory exists but contains no report.json."""

    @patch("regis.commands.analyze._discover_analyzers")
    def test_rerun_report_not_found(self, mock_discover):
        mock_discover.return_value = {"metadata": MetadataAnalyzer}

        runner = CliRunner()
        with runner.isolated_filesystem():
            empty_dir = Path("empty_report")
            empty_dir.mkdir()
            result = runner.invoke(
                main,
                ["analyze", "--rerun", "metadata", "--report", str(empty_dir)],
            )

        assert result.exit_code != 0
        assert "Report not found" in result.output


class TestRerunMetadataUpdatesReport:
    """Happy-path: metadata analyzer patches an existing report on disk."""

    @patch("regis.commands.analyze.validate_report")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_rerun_metadata_updates_report(self, mock_discover, mock_validate):
        mock_discover.return_value = {"metadata": MetadataAnalyzer}

        existing_report = {
            "version": "0.1.0",
            "request": {
                "registry": "r",
                "repository": "repo",
                "tag": "latest",
                "timestamp": "2024-01-01T00:00:00+00:00",
            },
            "results": {},
        }

        runner = CliRunner()
        with runner.isolated_filesystem():
            report_dir = Path("my_report")
            report_dir.mkdir()
            (report_dir / "report.json").write_text(
                json.dumps(existing_report), encoding="utf-8"
            )

            result = runner.invoke(
                main,
                [
                    "analyze",
                    "--rerun",
                    "metadata",
                    "--report",
                    str(report_dir),
                    "-m",
                    "PROJECT_ID=PROJ-42",
                ],
            )

            assert result.exit_code == 0, result.output

            updated = json.loads(
                (report_dir / "report.json").read_text(encoding="utf-8")
            )
            assert "metadata" in updated["results"]
            assert updated["metadata"]["PROJECT_ID"] == "PROJ-42"

    @patch("regis.commands.analyze.validate_report")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_rerun_metadata_result_contains_analyzer_key(
        self, mock_discover, mock_validate
    ):
        """The metadata result dict written to results["metadata"] should carry the
        "analyzer" key set to "metadata"."""
        mock_discover.return_value = {"metadata": MetadataAnalyzer}

        existing_report = {
            "version": "0.1.0",
            "request": {
                "registry": "r",
                "repository": "repo",
                "tag": "latest",
                "timestamp": "2024-01-01T00:00:00+00:00",
            },
            "results": {},
        }

        runner = CliRunner()
        with runner.isolated_filesystem():
            report_dir = Path("my_report")
            report_dir.mkdir()
            (report_dir / "report.json").write_text(
                json.dumps(existing_report), encoding="utf-8"
            )

            result = runner.invoke(
                main,
                [
                    "analyze",
                    "--rerun",
                    "metadata",
                    "--report",
                    str(report_dir),
                ],
            )

            assert result.exit_code == 0, result.output

            updated = json.loads(
                (report_dir / "report.json").read_text(encoding="utf-8")
            )
            assert updated["results"]["metadata"]["analyzer"] == "metadata"


class TestRerunReplaysPlaybookEvaluation:
    """Playbook re-evaluation must run during --rerun."""

    @patch("regis.commands.analyze.validate_report")
    @patch("regis.commands.analyze.run_playbooks")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_rerun_replays_playbook_evaluation(
        self, mock_discover, mock_run_playbooks, mock_validate
    ):
        mock_discover.return_value = {"metadata": MetadataAnalyzer}

        existing_report = {
            "version": "0.1.0",
            "request": {
                "registry": "r",
                "repository": "repo",
                "tag": "latest",
                "timestamp": "2024-01-01T00:00:00+00:00",
            },
            "results": {},
        }

        # run_playbooks must return a valid report-shaped dict so that
        # validate_report and subsequent writes don't blow up.
        mock_run_playbooks.return_value = {
            **existing_report,
            "results": {"metadata": {"analyzer": "metadata", "valid": True}},
        }

        runner = CliRunner()
        with runner.isolated_filesystem():
            report_dir = Path("my_report")
            report_dir.mkdir()
            (report_dir / "report.json").write_text(
                json.dumps(existing_report), encoding="utf-8"
            )

            result = runner.invoke(
                main,
                [
                    "analyze",
                    "--rerun",
                    "metadata",
                    "--report",
                    str(report_dir),
                ],
            )

            assert result.exit_code == 0, result.output
            mock_run_playbooks.assert_called_once()
