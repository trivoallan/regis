"""Tests for the CLI."""

import json
import re
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from regis.cli import main


class TestCliBasics:
    """Test basic CLI behavior."""

    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "regis" in result.output

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
        assert "oci" in result.output
        assert "versioning" in result.output

    def test_version_command(self):
        runner = CliRunner()
        result = runner.invoke(main, ["version"])
        assert result.exit_code == 0
        assert "regis version" in result.output
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

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_analyze_with_metadata(self, mock_discover, mock_client):
        from regis.analyzers.base import BaseAnalyzer

        class DummyAnalyzer(BaseAnalyzer):
            def analyze(self, client, repo, tag, platform=None):
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
            assert report["results"]["dummy"] == {
                "analyzer": "dummy",
                "repository": "library/nginx",
                "tag": "latest",
            }

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_analyze_with_nested_metadata(self, mock_discover, mock_client):
        from regis.analyzers.base import BaseAnalyzer

        class DummyAnalyzer(BaseAnalyzer):
            def analyze(self, client, repo, tag, platform=None):
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
            # request.metadata was removed (canonical location is top-level metadata)
            assert "metadata" not in report["request"]
            assert report["results"]["dummy"] == {
                "analyzer": "dummy",
                "repository": "library/nginx",
                "tag": "latest",
            }


class TestAnalyzeParallelism:
    """Test parallel analyzer execution."""

    def _make_dummy_analyzer(self, name: str):
        """Return a DummyAnalyzer class with the given name."""
        from regis.analyzers.base import BaseAnalyzer

        class DummyAnalyzer(BaseAnalyzer):
            analyzer_name = name

            def analyze(self, client, repo, tag, platform=None):
                return {"analyzer": self.analyzer_name, "repository": repo, "tag": tag}

            def validate(self, report):
                pass

        DummyAnalyzer.name = name
        return DummyAnalyzer

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
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

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
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

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
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

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_analyzer_failure_does_not_abort_others(self, mock_discover, mock_client):
        """A failing analyzer should be recorded as an error, not abort the run."""
        from regis.analyzers.base import AnalyzerError, BaseAnalyzer

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

    @patch("regis.commands.check.RegistryClient")
    def test_check_success(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.get_manifest.return_value = {"schemaVersion": 2}

        runner = CliRunner()
        result = runner.invoke(main, ["check", "nginx:latest"])

        assert result.exit_code == 0
        assert "Checking manifest availability" in result.output
        assert "Success! Manifest is accessible." in result.output
        mock_client.get_manifest.assert_called_once_with("latest")

    @patch("regis.commands.check.RegistryClient")
    def test_check_registry_error(self, mock_client_class):
        from regis.registry.client import RegistryError

        mock_client = mock_client_class.return_value
        mock_client.get_manifest.side_effect = RegistryError("Not found")

        runner = CliRunner()
        result = runner.invoke(main, ["check", "nginx:latest"])

        assert result.exit_code != 0
        assert "Registry error: Not found" in result.output

    @patch("regis.commands.check.RegistryClient")
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

    @patch("regis.commands.analyze.RegistryClient")
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
            # The legacy cached report had no schemaVersion; the cache-hit load
            # path must backfill it before validation, and the saved report
            # carries it.
            saved = json.loads((cache_dir / "report.json").read_text(encoding="utf-8"))
            assert saved["schemaVersion"] == 5

    @patch("regis.commands.analyze.render_presentation_templates")
    @patch("regis.commands.analyze.render_and_save_reports")
    @patch("regis.commands.analyze.validate_report")
    @patch("regis.commands.analyze.run_playbooks")
    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_analyze_fail_exits_on_breached_rules(
        self,
        mock_discover,
        mock_client,
        mock_playbooks,
        mock_validate,
        mock_render,
        mock_mr,
    ):
        from regis.analyzers.base import BaseAnalyzer

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


class TestAnalyzeSkip:
    """--skip option on regis analyze (issue #582)."""

    def _make_dummy_analyzer(self, name: str):
        from regis.analyzers.base import BaseAnalyzer

        class DummyAnalyzer(BaseAnalyzer):
            analyzer_name = name

            def analyze(self, client, repo, tag, platform=None):
                return {"analyzer": self.analyzer_name, "repository": repo, "tag": tag}

            def validate(self, report):
                pass

        DummyAnalyzer.name = name
        return DummyAnalyzer

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_skip_excludes_named_analyzer(self, mock_discover, mock_client):
        mock_discover.return_value = {
            "a": self._make_dummy_analyzer("a"),
            "b": self._make_dummy_analyzer("b"),
            "c": self._make_dummy_analyzer("c"),
        }
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["analyze", "nginx:latest", "--skip", "b"])
        assert result.exit_code == 0
        completed = [
            line for line in result.output.splitlines() if line.startswith("  ✓ ")
        ]
        # Each line is "  ✓ <name>  (<elapsed>s)" — the analyzer name is the
        # second whitespace-separated token.
        completed_names = [line.split()[1] for line in completed]
        assert "b" not in completed_names
        assert "a" in completed_names and "c" in completed_names

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_skip_repeatable(self, mock_discover, mock_client):
        mock_discover.return_value = {
            "a": self._make_dummy_analyzer("a"),
            "b": self._make_dummy_analyzer("b"),
            "c": self._make_dummy_analyzer("c"),
        }
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main, ["analyze", "nginx:latest", "--skip", "a", "--skip", "c"]
            )
        assert result.exit_code == 0
        assert "Running 1 analyzer(s)" in result.output

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_skip_unknown_warns_but_succeeds(self, mock_discover, mock_client):
        mock_discover.return_value = {"a": self._make_dummy_analyzer("a")}
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["analyze", "nginx:latest", "--skip", "nope"])
        assert result.exit_code == 0
        assert "unknown analyzer 'nope'" in result.output

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_skip_all_fails(self, mock_discover, mock_client):
        mock_discover.return_value = {"a": self._make_dummy_analyzer("a")}
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["analyze", "nginx:latest", "--skip", "a"])
        assert result.exit_code != 0
        assert "All analyzers were skipped" in result.output


class TestAnalyzeEnvVars:
    """Environment variable support on regis analyze (issue #583)."""

    def _make_dummy_analyzer(self, name: str):
        from regis.analyzers.base import BaseAnalyzer

        class DummyAnalyzer(BaseAnalyzer):
            analyzer_name = name

            def analyze(self, client, repo, tag, platform=None):
                DummyAnalyzer.last_platform = platform
                return {"analyzer": self.analyzer_name, "repository": repo, "tag": tag}

            def validate(self, report):
                pass

        DummyAnalyzer.name = name
        DummyAnalyzer.last_platform = None
        return DummyAnalyzer

    def test_help_advertises_env_vars(self):
        runner = CliRunner()
        result = runner.invoke(main, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "REGIS_PLAYBOOK" in result.output
        assert "REGIS_PLATFORM" in result.output
        assert "REGIS_OUTPUT_DIR" in result.output
        assert "REGIS_MAX_WORKERS" in result.output

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_regis_platform_env(self, mock_discover, mock_client):
        cls = self._make_dummy_analyzer("dummy")
        mock_discover.return_value = {"dummy": cls}
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                ["analyze", "nginx:latest"],
                env={"REGIS_PLATFORM": "linux/arm64"},
            )
        assert result.exit_code == 0
        assert cls.last_platform == "linux/arm64"

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_cli_flag_overrides_env(self, mock_discover, mock_client):
        cls = self._make_dummy_analyzer("dummy")
        mock_discover.return_value = {"dummy": cls}
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                ["analyze", "nginx:latest", "--platform", "linux/amd64"],
                env={"REGIS_PLATFORM": "linux/arm64"},
            )
        assert result.exit_code == 0
        assert cls.last_platform == "linux/amd64"

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_regis_max_workers_env(self, mock_discover, mock_client):
        cls = self._make_dummy_analyzer("dummy")
        mock_discover.return_value = {"dummy": cls}
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                ["analyze", "nginx:latest"],
                env={"REGIS_MAX_WORKERS": "2"},
            )
        assert result.exit_code == 0
        assert "1 worker(s)" in result.output


class TestQuietFlag:
    """Top-level --quiet / -q flag (issue #584)."""

    def _make_dummy_analyzer(self, name: str):
        from regis.analyzers.base import BaseAnalyzer

        class DummyAnalyzer(BaseAnalyzer):
            analyzer_name = name

            def analyze(self, client, repo, tag, platform=None):
                return {"analyzer": self.analyzer_name, "repository": repo, "tag": tag}

            def validate(self, report):
                pass

        DummyAnalyzer.name = name
        return DummyAnalyzer

    def test_help_advertises_quiet(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "--quiet" in result.output

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_quiet_suppresses_progress_lines(self, mock_discover, mock_client):
        mock_discover.return_value = {"dummy": self._make_dummy_analyzer("dummy")}
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            import importlib.resources

            pb = importlib.resources.files("regis") / "playbooks" / "default"
            result = runner.invoke(
                main,
                ["-q", "analyze", "nginx:latest", "--playbook", str(pb)],
            )
        assert result.exit_code == 0
        assert "Running" not in result.output
        assert "✓ dummy" not in result.output
        assert "Analyzing" not in result.output
        assert "Report (json) written to" not in result.output
        # --quiet also suppresses the post-run verdict block
        assert "/100" not in result.output

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_default_keeps_progress_lines(self, mock_discover, mock_client):
        mock_discover.return_value = {"dummy": self._make_dummy_analyzer("dummy")}
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["analyze", "nginx:latest"])
        assert result.exit_code == 0
        assert "Analyzing" in result.output or "Running" in result.output

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_quiet_still_emits_analyzer_failure(self, mock_discover, mock_client):
        from regis.analyzers.base import AnalyzerError, BaseAnalyzer

        class FailingAnalyzer(BaseAnalyzer):
            name = "failing"

            def analyze(self, client, repo, tag, platform=None):
                raise AnalyzerError("boom")

            def validate(self, report):
                pass

        mock_discover.return_value = {"failing": FailingAnalyzer}
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["-q", "analyze", "nginx:latest"])
        assert "✗ failing" in result.output
        assert "Running" not in result.output
        assert "Analyzing" not in result.output


class TestAnalyzerProgressFeedback:
    """Per-analyzer progress with timing (issue #581)."""

    def _make_dummy_analyzer(self, name: str):
        from regis.analyzers.base import BaseAnalyzer

        class DummyAnalyzer(BaseAnalyzer):
            analyzer_name = name

            def analyze(self, client, repo, tag, platform=None):
                return {"analyzer": self.analyzer_name, "repository": repo, "tag": tag}

            def validate(self, report):
                pass

        DummyAnalyzer.name = name
        return DummyAnalyzer

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_success_lines_include_timing(self, mock_discover, mock_client):
        mock_discover.return_value = {
            "alpha": self._make_dummy_analyzer("alpha"),
            "bravo": self._make_dummy_analyzer("bravo"),
        }
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["analyze", "nginx:latest"])
        assert result.exit_code == 0
        success_lines = [line for line in result.output.splitlines() if "✓" in line]
        assert len(success_lines) == 2
        for line in success_lines:
            assert re.search(r"\(\d+\.\d+s\)", line)

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_running_banner_present(self, mock_discover, mock_client):
        mock_discover.return_value = {"dummy": self._make_dummy_analyzer("dummy")}
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["analyze", "nginx:latest"])
        assert result.exit_code == 0
        assert "Running 1 analyzer(s)" in result.output

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_failure_line_also_shows_timing(self, mock_discover, mock_client):
        from regis.analyzers.base import AnalyzerError, BaseAnalyzer

        class FailingAnalyzer(BaseAnalyzer):
            name = "failing"

            def analyze(self, client, repo, tag, platform=None):
                raise AnalyzerError("boom")

            def validate(self, report):
                pass

        mock_discover.return_value = {"failing": FailingAnalyzer}
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["analyze", "nginx:latest"])
        failing_lines = [
            line for line in result.output.splitlines() if "✗ failing" in line
        ]
        assert len(failing_lines) == 1
        assert re.search(r"\(\d+\.\d+s\)", failing_lines[0])


class TestAnalyzeSummary:
    """One-line analysis summary printed after run (issue #585)."""

    def _make_dummy_analyzer(self, name: str):
        from regis.analyzers.base import BaseAnalyzer

        class DummyAnalyzer(BaseAnalyzer):
            analyzer_name = name

            def analyze(self, client, repo, tag, platform=None):
                return {"analyzer": self.analyzer_name, "repository": repo, "tag": tag}

            def validate(self, report):
                pass

        DummyAnalyzer.name = name
        return DummyAnalyzer

    def test_render_verdict_block_passed_only(self, capsys):
        from regis.commands.analyze import _render_verdict_block

        _render_verdict_block(
            {
                "playbooks": [
                    {
                        "tier": "Gold",
                        "tier_icon": "🥇",
                        "rules_summary": {"score": 100, "total": 2, "passed": 2},
                        "rules": [
                            {
                                "slug": "a",
                                "passed": True,
                                "level": "info",
                                "status": "passed",
                                "message": "",
                            },
                            {
                                "slug": "b",
                                "passed": True,
                                "level": "info",
                                "status": "passed",
                                "message": "",
                            },
                        ],
                        "badge_labels": [],
                    }
                ]
            },
            quiet=False,
        )
        import re

        out = re.sub(r"\x1b\[[0-9;]*m", "", capsys.readouterr().err)
        assert "🥇 Gold · 100/100" in out
        assert "all pass ✓" in out
        assert "✗" not in out

    def test_render_verdict_block_failed_rules_listed(self, capsys):
        import re

        from regis.commands.analyze import _render_verdict_block

        _render_verdict_block(
            {
                "playbooks": [
                    {
                        "tier": "Bronze",
                        "tier_icon": "🥉",
                        "rules_summary": {"score": 33, "total": 3, "passed": 1},
                        "rules": [
                            {
                                "slug": "a",
                                "passed": True,
                                "level": "info",
                                "status": "passed",
                                "message": "",
                            },
                            {
                                "slug": "trivy.no-critical-cves",
                                "passed": False,
                                "level": "critical",
                                "status": "failed",
                                "message": "2 critical CVEs found",
                            },
                            {
                                "slug": "freshness.max-age-days",
                                "passed": False,
                                "level": "warning",
                                "status": "failed",
                                "message": "Image is 120 days old (max: 90)",
                            },
                        ],
                        "badge_labels": [],
                    }
                ]
            },
            quiet=False,
        )
        out = re.sub(r"\x1b\[[0-9;]*m", "", capsys.readouterr().err)
        assert "🥉 Bronze · 33/100" in out
        assert "2 failed" in out
        assert "[trivy.no-critical-cves]" in out
        assert "2 critical CVEs found" in out
        assert "[freshness.max-age-days]" in out

    def test_render_verdict_block_no_playbooks_silent(self, capsys):
        from regis.commands.analyze import _render_verdict_block

        _render_verdict_block({}, quiet=False)
        _render_verdict_block({"playbooks": []}, quiet=False)
        assert capsys.readouterr().err == ""

    def test_render_verdict_block_aligns_messages(self, capsys):
        """Messages line up regardless of differing slug lengths."""
        import re

        from regis.commands.analyze import _render_verdict_block

        _render_verdict_block(
            {
                "playbooks": [
                    {
                        "tier": "Bronze",
                        "tier_icon": "🥉",
                        "rules_summary": {"score": 33, "total": 2, "passed": 0},
                        "rules": [
                            {
                                "slug": "cve-high",
                                "passed": False,
                                "level": "high",
                                "status": "failed",
                                "message": "msg one",
                            },
                            {
                                "slug": "scorecard-min",
                                "passed": False,
                                "level": "warning",
                                "status": "failed",
                                "message": "msg two",
                            },
                        ],
                        "badge_labels": [],
                    }
                ]
            },
            quiet=False,
        )
        out = re.sub(r"\x1b\[[0-9;]*m", "", capsys.readouterr().err)
        rule_lines = [ln for ln in out.splitlines() if ln.lstrip().startswith("✗")]
        assert len(rule_lines) == 2
        # The message text starts at the same column on every rule line.
        cols = [ln.index("msg ") for ln in rule_lines]
        assert cols[0] == cols[1]
        # The slug tag likewise lines up under a fixed column.
        slug_cols = [ln.index("[") for ln in rule_lines]
        assert slug_cols[0] == slug_cols[1]

    def test_render_verdict_block_shows_severity(self, capsys):
        """Each rule line carries its severity (emoji + level word)."""
        import re

        from regis.commands.analyze import _render_verdict_block

        _render_verdict_block(
            {
                "playbooks": [
                    {
                        "tier": "Bronze",
                        "tier_icon": "🥉",
                        "rules_summary": {"score": 33, "total": 2, "passed": 0},
                        "rules": [
                            {
                                "slug": "cve-critical",
                                "passed": False,
                                "level": "critical",
                                "status": "failed",
                                "message": "boom",
                            },
                            {
                                "slug": "age",
                                "passed": False,
                                "level": "warning",
                                "status": "failed",
                                "message": "old",
                            },
                        ],
                        "badge_labels": [],
                    }
                ]
            },
            quiet=False,
        )
        out = re.sub(r"\x1b\[[0-9;]*m", "", capsys.readouterr().err)
        assert "🟥 critical" in out
        assert "🟧 warning" in out

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_analyze_prints_summary_when_playbook_given(
        self, mock_discover, mock_client
    ):
        import importlib.resources

        mock_discover.return_value = {"dummy": self._make_dummy_analyzer("dummy")}
        mock_client.return_value.get_digest.return_value = None

        pb = importlib.resources.files("regis") / "playbooks" / "default"
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                ["analyze", "nginx:latest", "--playbook", str(pb)],
            )
        assert result.exit_code == 0
        # The verdict block replaces the old "Playbook · " summary line.
        assert "/100" in result.output

    @patch("regis.commands.analyze.RegistryClient")
    @patch("regis.commands.analyze._discover_analyzers")
    def test_analyze_silent_without_playbook(self, mock_discover, mock_client):
        mock_discover.return_value = {"dummy": self._make_dummy_analyzer("dummy")}
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["analyze", "nginx:latest"])
        assert result.exit_code == 0
        # The verdict block is printed by default (even without explicit --playbook).
        # The old "Playbook · " line is no longer used; the new block uses tier · score.
        assert "/100" in result.output


def test_cli_discovery_uses_entry_point_provider():
    """The CLI consults the AnalyzerProvider port for discovery."""
    from regis.adapters.driven.analyzers.entry_point_provider import (
        EntryPointAnalyzerProvider,
    )
    from regis.analyzers.discovery import discover_analyzers
    from regis.commands import analyze as analyze_mod

    assert isinstance(analyze_mod._analyzer_provider, EntryPointAnalyzerProvider)
    assert dict(analyze_mod._discover_analyzers()) == dict(discover_analyzers())
