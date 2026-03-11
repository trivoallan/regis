# trunk-ignore-all(bandit/B101)
"""Tests for the CLI."""

import json
import re
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from regis_cli.cli import main


class TestCliBasics:
    """Test basic CLI behavior."""

    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "regis-cli" in result.output

    def test_analyze_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "URL" in result.output

    def test_list_command(self):
        runner = CliRunner()
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0
        # The built-in analyzers should appear.
        assert "skopeo" in result.output
        assert "versioning" in result.output

    def test_version_command(self):
        runner = CliRunner()
        result = runner.invoke(main, ["version"])
        assert result.exit_code == 0
        assert "regis-cli version" in result.output
        assert re.search(r"\d+\.\d+\.\d+", result.output)

    def test_analyze_invalid_url(self):
        runner = CliRunner()
        result = runner.invoke(main, ["analyze", "https://myregistry.example.com/"])
        assert result.exit_code != 0

    def test_analyze_unknown_analyzer(self):
        runner = CliRunner()
        result = runner.invoke(main, ["analyze", "nginx", "-a", "nonexistent"])
        assert result.exit_code != 0
        assert "Unknown analyzer" in result.output

    @patch("regis_cli.cli.RegistryClient")
    @patch("regis_cli.cli._discover_analyzers")
    def test_analyze_with_metadata(self, mock_discover, mock_client):
        from regis_cli.analyzers.base import BaseAnalyzer

        class DummyAnalyzer(BaseAnalyzer):
            def analyze(self, client, repo, tag):
                return {"analyzer": "dummy", "repository": repo, "tag": tag}

            def validate(self, report):
                pass

        mock_discover.return_value = {"dummy": DummyAnalyzer}
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "analyze",
                    "nginx:latest",
                    "--meta",
                    "build=123",
                    "--meta",
                    "env=prod",
                    "--meta",
                    "flag_only",
                ],
            )
            assert result.exit_code == 0

            report_file = Path(
                "reports/registry-1.docker.io/library-nginx/latest/report.json"
            )
            report = json.loads(report_file.read_text(encoding="utf-8"))

            assert "metadata" in report
            assert report["metadata"]["build"] == "123"
            assert report["metadata"]["env"] == "prod"
            assert report["metadata"]["flag_only"] == "true"

    @patch("regis_cli.cli.RegistryClient")
    @patch("regis_cli.cli._discover_analyzers")
    def test_analyze_with_nested_metadata(self, mock_discover, mock_client):
        from regis_cli.analyzers.base import BaseAnalyzer

        class DummyAnalyzer(BaseAnalyzer):
            def analyze(self, client, repo, tag):
                return {"analyzer": "dummy", "repository": repo, "tag": tag}

            def validate(self, report):
                pass

        mock_discover.return_value = {"dummy": DummyAnalyzer}
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "analyze",
                    "nginx:latest",
                    "--meta",
                    "ci.job_id=456",
                    "--meta",
                    "ci.url=http://ci.com",
                    "--meta",
                    "project=regis",
                ],
            )
            assert result.exit_code == 0

            report_file = Path(
                "reports/registry-1.docker.io/library-nginx/latest/report.json"
            )
            report = json.loads(report_file.read_text(encoding="utf-8"))

            assert "metadata" in report
            assert report["metadata"]["ci"]["job_id"] == "456"
            assert report["metadata"]["ci"]["url"] == "http://ci.com"
            assert report["metadata"]["project"] == "regis"
            # Also check request metadata
            assert report["request"]["metadata"]["ci"]["job_id"] == "456"

    @patch("regis_cli.cli.RegistryClient")
    @patch("regis_cli.cli._discover_analyzers")
    def test_analyze_html_with_metadata(self, mock_discover, mock_client):
        from regis_cli.analyzers.base import BaseAnalyzer

        class DummyAnalyzer(BaseAnalyzer):
            def analyze(self, client, repo, tag):
                return {"analyzer": "dummy", "repository": repo, "tag": tag}

            def validate(self, report):
                pass

        mock_discover.return_value = {"dummy": DummyAnalyzer}
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "analyze",
                    "nginx:latest",
                    "--site",
                    "--meta",
                    "build=123",
                    "--meta",
                    "env=prod",
                ],
            )
            assert result.exit_code == 0

            # Default HTML report filename is index.html (from first page of default playbook)
            report_file = Path(
                "reports/registry-1.docker.io/library-nginx/latest/index.html"
            )
            html_content = report_file.read_text(encoding="utf-8")

            assert "build" in html_content
            assert "123" in html_content
            assert "env" in html_content
            assert "prod" in html_content


class TestCliCheck:
    """Test the check command."""

    @patch("regis_cli.cli.RegistryClient")
    def test_check_success(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.get_manifest.return_value = {"schemaVersion": 2}

        runner = CliRunner()
        result = runner.invoke(main, ["check", "nginx:latest"])

        assert result.exit_code == 0
        assert "Checking manifest availability" in result.output
        assert "Success! Manifest is accessible." in result.output
        mock_client.get_manifest.assert_called_once_with("latest")

    @patch("regis_cli.cli.RegistryClient")
    def test_check_registry_error(self, mock_client_class):
        from regis_cli.registry.client import RegistryError

        mock_client = mock_client_class.return_value
        mock_client.get_manifest.side_effect = RegistryError("Not found")

        runner = CliRunner()
        result = runner.invoke(main, ["check", "nginx:latest"])

        assert result.exit_code != 0
        assert "Registry error: Not found" in result.output

    @patch("regis_cli.cli.RegistryClient")
    def test_check_empty_manifest(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.get_manifest.return_value = {}

        runner = CliRunner()
        result = runner.invoke(main, ["check", "nginx:latest"])

        assert result.exit_code != 0
        assert "Received empty manifest" in result.output

    def test_check_invalid_url(self):
        runner = CliRunner()
        result = runner.invoke(main, ["check", "https://not-a-registry"])

        assert result.exit_code != 0
