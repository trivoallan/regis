"""Tests for 'regis-cli archive' command group."""

import json

from click.testing import CliRunner

from regis_cli.cli import main


class TestArchiveAdd:
    def test_happy_path(self, tmp_path):
        report_file = tmp_path / "report.json"
        report_file.write_text(
            json.dumps(
                {
                    "request": {
                        "registry": "docker.io",
                        "repository": "library/nginx",
                        "tag": "latest",
                        "timestamp": "2024-01-15T10:00:00+00:00",
                    }
                }
            ),
            encoding="utf-8",
        )
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["archive", "add", str(report_file), "-A", str(archive_dir)],
        )

        assert result.exit_code == 0, result.output
        assert "Archived to" in result.output
        assert "Manifest updated" in result.output
        assert (archive_dir / "manifest.json").exists()

    def test_invalid_json_fails(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json", encoding="utf-8")
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["archive", "add", str(bad_file), "-A", str(archive_dir)],
        )

        assert result.exit_code != 0
        assert "Could not read" in result.output

    def test_nonexistent_report_file_fails(self, tmp_path):
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["archive", "add", str(tmp_path / "ghost.json"), "-A", str(archive_dir)],
        )

        assert result.exit_code != 0

    def test_archive_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["archive", "--help"])
        assert result.exit_code == 0
        assert "add" in result.output
