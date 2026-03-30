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

    @patch("regis_cli.commands.analyze.RegistryClient")
    @patch("regis_cli.commands.analyze._discover_analyzers")
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

    @patch("regis_cli.commands.analyze.RegistryClient")
    @patch("regis_cli.commands.analyze._discover_analyzers")
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

    @patch("regis_cli.commands.analyze.RegistryClient")
    @patch("regis_cli.commands.analyze._discover_analyzers")
    @patch("regis_cli.report.docusaurus.build_report_site")
    def test_analyze_html_with_metadata(
        self, mock_build_site, mock_discover, mock_client
    ):
        # Mock build_report_site to only write the report.json file,
        # avoiding the heavy Docusaurus/npm build process during unit tests.
        def side_effect(report, output_dir, **kwargs):
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "report.json").write_text(
                json.dumps(report), encoding="utf-8"
            )

        mock_build_site.side_effect = side_effect
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

            # Report data is written to report.json alongside the static SPA
            report_file = Path(
                "reports/registry-1.docker.io/library-nginx/latest/report.json"
            )
            report_data = json.loads(report_file.read_text(encoding="utf-8"))

            assert "metadata" in report_data
            assert report_data["metadata"]["build"] == "123"
            assert report_data["metadata"]["env"] == "prod"


class TestAnalyzeParallelism:
    """Test parallel analyzer execution."""

    def _make_dummy_analyzer(self, name: str, delay: float = 0.0):
        """Return a DummyAnalyzer class with the given name."""
        import time

        from regis_cli.analyzers.base import BaseAnalyzer

        class DummyAnalyzer(BaseAnalyzer):
            analyzer_name = name

            def analyze(self, client, repo, tag, platform=None):
                if delay:
                    time.sleep(delay)
                return {"analyzer": self.analyzer_name, "repository": repo, "tag": tag}

            def validate(self, report):
                pass

        DummyAnalyzer.name = name
        return DummyAnalyzer

    @patch("regis_cli.commands.analyze.RegistryClient")
    @patch("regis_cli.commands.analyze._discover_analyzers")
    def test_parallel_analyzers_all_succeed(self, mock_discover, mock_client):
        analyzers = {
            f"dummy{i}": self._make_dummy_analyzer(f"dummy{i}") for i in range(3)
        }
        mock_discover.return_value = analyzers
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main, ["analyze", "nginx:latest", "--max-workers", "3"]
            )
        assert result.exit_code == 0
        for i in range(3):
            assert f"dummy{i}" in result.output

    @patch("regis_cli.commands.analyze.RegistryClient")
    @patch("regis_cli.commands.analyze._discover_analyzers")
    def test_max_workers_capped_at_analyzer_count(self, mock_discover, mock_client):
        """max_workers should not exceed the number of selected analyzers."""
        mock_discover.return_value = {"dummy": self._make_dummy_analyzer("dummy")}
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main, ["analyze", "nginx:latest", "--max-workers", "10"]
            )
        assert result.exit_code == 0
        assert "1 worker(s)" in result.output

    @patch("regis_cli.commands.analyze.RegistryClient")
    @patch("regis_cli.commands.analyze._discover_analyzers")
    def test_serial_execution_with_max_workers_1(self, mock_discover, mock_client):
        mock_discover.return_value = {"dummy": self._make_dummy_analyzer("dummy")}
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main, ["analyze", "nginx:latest", "--max-workers", "1"]
            )
        assert result.exit_code == 0
        assert "1 worker(s)" in result.output

    @patch("regis_cli.commands.analyze.RegistryClient")
    @patch("regis_cli.commands.analyze._discover_analyzers")
    def test_analyzer_failure_does_not_abort_others(self, mock_discover, mock_client):
        """A failing analyzer should be recorded as an error, not abort the run."""
        from regis_cli.analyzers.base import AnalyzerError, BaseAnalyzer

        class FailingAnalyzer(BaseAnalyzer):
            name = "failing"

            def analyze(self, client, repo, tag, platform=None):
                raise AnalyzerError("boom")

            def validate(self, report):
                pass

        mock_discover.return_value = {
            "dummy": self._make_dummy_analyzer("dummy"),
            "failing": FailingAnalyzer,
        }
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["analyze", "nginx:latest"])
        assert result.exit_code == 0
        assert "✗ failing" in result.output
        assert "✓ dummy" in result.output


class TestCliCheck:
    """Test the check command."""

    @patch("regis_cli.commands.check.RegistryClient")
    def test_check_success(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.get_manifest.return_value = {"schemaVersion": 2}

        runner = CliRunner()
        result = runner.invoke(main, ["check", "nginx:latest"])

        assert result.exit_code == 0
        assert "Checking manifest availability" in result.output
        assert "Success! Manifest is accessible." in result.output
        mock_client.get_manifest.assert_called_once_with("latest")

    @patch("regis_cli.commands.check.RegistryClient")
    def test_check_registry_error(self, mock_client_class):
        from regis_cli.registry.client import RegistryError

        mock_client = mock_client_class.return_value
        mock_client.get_manifest.side_effect = RegistryError("Not found")

        runner = CliRunner()
        result = runner.invoke(main, ["check", "nginx:latest"])

        assert result.exit_code != 0
        assert "Registry error: Not found" in result.output

    @patch("regis_cli.commands.check.RegistryClient")
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


class TestEvaluateCmd:
    """Tests for the `evaluate` subcommand."""

    def test_evaluate_basic(self, tmp_path):
        report = {
            "version": "0.22.0",
            "request": {
                "url": "nginx:latest",
                "registry": "registry-1.docker.io",
                "repository": "library/nginx",
                "tag": "latest",
                "digest": "latest",
                "analyzers": [],
                "timestamp": "2024-01-01T00:00:00+00:00",
            },
            "results": {},
        }
        report_file = tmp_path / "report.json"
        report_file.write_text(json.dumps(report))

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["evaluate", str(report_file)])
        assert result.exit_code == 0

    def test_evaluate_missing_results_key(self, tmp_path):
        bad_report = {"version": "0.22.0", "not_results": {}}
        report_file = tmp_path / "bad.json"
        report_file.write_text(json.dumps(bad_report))

        runner = CliRunner()
        result = runner.invoke(main, ["evaluate", str(report_file)])
        assert result.exit_code != 0
        assert "missing 'results'" in result.output

    def test_evaluate_invalid_json(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json {{{")

        runner = CliRunner()
        result = runner.invoke(main, ["evaluate", str(bad_file)])
        assert result.exit_code != 0
        assert "Failed to load" in result.output


class TestAnalyzeCacheAndFail:
    """Tests for --cache and --fail options of the `analyze` command."""

    @patch("regis_cli.commands.analyze.RegistryClient")
    def test_analyze_cache_hit_skips_analyzers(self, mock_client):
        mock_client.return_value.get_digest.return_value = "sha256:abc123"
        cached_report = {
            "version": "0.22.0",
            "request": {
                "url": "nginx:latest",
                "registry": "registry-1.docker.io",
                "repository": "library/nginx",
                "tag": "latest",
                "digest": "sha256-abc123",
                "analyzers": [],
                "timestamp": "2024-01-01T00:00:00+00:00",
            },
            "results": {},
        }
        runner = CliRunner()
        with runner.isolated_filesystem():
            cache_dir = Path("reports/registry-1.docker.io/library-nginx/sha256-abc123")
            cache_dir.mkdir(parents=True)
            (cache_dir / "report.json").write_text(json.dumps(cached_report))

            result = runner.invoke(main, ["analyze", "nginx:latest", "--cache"])

        assert result.exit_code == 0
        assert "cached" in result.output

    @patch("regis_cli.commands.analyze.render_mr_templates")
    @patch("regis_cli.commands.analyze.render_and_save_reports")
    @patch("regis_cli.commands.analyze.validate_report")
    @patch("regis_cli.commands.analyze.run_playbooks")
    @patch("regis_cli.commands.analyze.RegistryClient")
    @patch("regis_cli.commands.analyze._discover_analyzers")
    def test_analyze_fail_exits_on_breached_rules(
        self,
        mock_discover,
        mock_client,
        mock_playbooks,
        mock_validate,
        mock_render,
        mock_mr,
    ):
        from regis_cli.analyzers.base import BaseAnalyzer

        class DummyAnalyzer(BaseAnalyzer):
            def analyze(self, client, repo, tag, platform=None):
                return {"analyzer": "dummy"}

            def validate(self, report):
                pass

        mock_discover.return_value = {"dummy": DummyAnalyzer}
        mock_client.return_value.get_digest.return_value = None
        mock_playbooks.return_value = {
            "version": "0.22.0",
            "request": {},
            "results": {},
            "playbooks": [
                {
                    "rules": [{"passed": False, "level": "critical", "slug": "rule-x"}],
                    "rules_summary": {},
                    "tier": None,
                    "badges": [],
                }
            ],
            "rules": [{"passed": False, "level": "critical", "slug": "rule-x"}],
        }

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main, ["analyze", "nginx:latest", "--evaluate", "--fail"]
            )

        assert result.exit_code == 1
        assert "rule breaches" in result.output
