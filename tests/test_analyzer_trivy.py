from unittest.mock import MagicMock, patch

import pytest

from regis_cli.analyzers.base import AnalyzerError
from regis_cli.analyzers.trivy import TrivyAnalyzer, _run_trivy


class TestTrivyAnalyzer:
    @patch("regis_cli.analyzers.trivy.shutil.which")
    @patch("regis_cli.analyzers.trivy.subprocess.run")
    def test_run_trivy_env_and_platform(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/trivy"
        mock_run.return_value = MagicMock(stdout="{}", check_returncode=lambda: None)

        # Test creds mapping to env (line 37-38) and platform handling (line 49)
        _run_trivy("image", username="user", password="pwd", platform="linux/arm64")

        args = mock_run.call_args[0][0]
        env = mock_run.call_args[1]["env"]
        assert "--platform" in args
        assert "linux/arm64" in args
        assert env["TRIVY_USERNAME"] == "user"
        assert env["TRIVY_PASSWORD"] == "pwd"

    @patch("regis_cli.analyzers.trivy.shutil.which")
    @patch("regis_cli.analyzers.trivy.subprocess.run")
    def test_run_trivy_invalid_json(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/trivy"
        mock_run.return_value = MagicMock(stdout="not-json")
        # Hit line 65-66
        with pytest.raises(AnalyzerError, match="invalid JSON"):
            _run_trivy("image")

    @patch("regis_cli.analyzers.trivy._run_trivy")
    def test_analyze_error_forwarding(self, mock_run_trivy):
        # Hit line 98-103
        mock_run_trivy.side_effect = AnalyzerError("boom")
        analyzer = TrivyAnalyzer()
        client = MagicMock()
        client.registry = "example.com"
        with pytest.raises(AnalyzerError, match="boom"):
            analyzer.analyze(client, "repo", "tag")

    @patch("regis_cli.analyzers.trivy._run_trivy")
    def test_analyze_vuln_processing(self, mock_run_trivy):
        mock_run_trivy.return_value = {
            "SchemaVersion": 2,
            "Results": [
                {
                    "Target": "app.jar",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-1",
                            "Severity": "CRITICAL",
                            "PkgName": "lib",
                        },
                        {
                            "VulnerabilityID": "CVE-2",
                            "Severity": "HIGH",
                            "PkgName": "lib2",
                        },
                    ],
                },
                {"Target": "no-vulns", "Vulnerabilities": []},
            ],
        }
        analyzer = TrivyAnalyzer()
        client = MagicMock()
        client.registry = "docker.io"
        report = analyzer.analyze(client, "myrepo", "tag")
        assert report["critical_count"] == 1
        assert report["high_count"] == 1
        assert report["vulnerability_count"] == 2
        assert len(report["targets"]) == 2
        # Hit line 141 (None vulnerabilities)
        assert report["targets"][1]["Vulnerabilities"] is None
