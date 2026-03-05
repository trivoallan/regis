import json
import os
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from regis_cli.cli import main
from regis_cli.registry.auth import resolve_credentials


class TestGithubEnvironment:
    """Simulate GitHub/CI environment interactions."""

    def test_auth_resolution_from_env(self):
        """Test that registry/auth.py correctly picks up variables."""
        # Domain-specific override
        with patch.dict(
            os.environ,
            {
                "REGIS_AUTH_GHCR_IO_USERNAME": "bot",
                "REGIS_AUTH_GHCR_IO_PASSWORD": "token",
            },
        ):
            user, pwd = resolve_credentials("ghcr.io")
            assert user == "bot"
            assert pwd == "token"

        # Global fallback
        with patch.dict(
            os.environ, {"REGIS_USERNAME": "global", "REGIS_PASSWORD": "secret"}
        ):
            # Clear caches if any or just ensure no domain-specific matches
            user, pwd = resolve_credentials("other.registry.io")
            assert user == "global"
            assert pwd == "secret"

    @patch("regis_cli.cli.RegistryClient")
    @patch("regis_cli.cli._discover_analyzers")
    def test_cli_with_mocked_gh_metadata(self, mock_discover, mock_client):
        """Test the CLI when called with GitHub-like environment variables via --meta."""
        from regis_cli.analyzers.base import BaseAnalyzer

        class DummyAnalyzer(BaseAnalyzer):
            def analyze(self, client, repo, tag, platform=None):
                return {"analyzer": "dummy", "passed": True}

            def validate(self, report):
                pass

        mock_discover.return_value = {"dummy": DummyAnalyzer}
        mock_client.return_value.get_digest.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Simulate a call from GitHub Actions:
            # regis-cli analyze $IMAGE --meta trigger.user=${{ github.actor }} ...
            result = runner.invoke(
                main,
                [
                    "analyze",
                    "myrepo:tag",
                    "--meta",
                    "trigger.user=github-bot",
                    "--meta",
                    "trigger.url=https://github.com/org/repo/actions/runs/12345",
                    "--meta",
                    "ci.job_id=999",
                ],
            )
            assert result.exit_code == 0

            report_file = Path(
                "reports/registry-1.docker.io/library-myrepo/tag/report.json"
            )
            report = json.loads(report_file.read_text(encoding="utf-8"))

            assert report["metadata"]["trigger"]["user"] == "github-bot"
            assert (
                report["metadata"]["trigger"]["url"]
                == "https://github.com/org/repo/actions/runs/12345"
            )
            assert report["metadata"]["ci"]["job_id"] == "999"
