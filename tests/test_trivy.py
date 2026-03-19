"""Tests for Trivy analyzer."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from regis_cli.analyzers.base import AnalyzerError
from regis_cli.analyzers.trivy import TrivyAnalyzer, _run_trivy


class TestRunTrivy:
    """Tests for _run_trivy helper."""

    @patch("regis_cli.analyzers.trivy.shutil.which")
    def test_trivy_not_found(self, mock_which):
        mock_which.return_value = None
        with pytest.raises(AnalyzerError, match="trivy executable not found"):
            _run_trivy("alpine:latest")

    @patch("regis_cli.analyzers.trivy.shutil.which")
    @patch("regis_cli.analyzers.trivy.subprocess.run")
    def test_success(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/trivy"
        mock_run.return_value.stdout = '{"SchemaVersion": 2, "Results": []}'

        result = _run_trivy("alpine:latest")
        assert result == {"SchemaVersion": 2, "Results": []}

        args = mock_run.call_args[0][0]
        assert args[0] == "/usr/local/bin/trivy"
        assert "alpine:latest" in args

    @patch("regis_cli.analyzers.trivy.shutil.which")
    @patch("regis_cli.analyzers.trivy.subprocess.run")
    def test_failure(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/trivy"
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["trivy"], stderr="error message"
        )

        with pytest.raises(AnalyzerError, match="trivy failed: error message"):
            _run_trivy("alpine:latest")


class TestTrivyAnalyzer:
    """Tests for TrivyAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        return TrivyAnalyzer()

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client.registry = "registry-1.docker.io"
        return client

    @patch("regis_cli.analyzers.trivy._run_trivy")
    def test_analyze_success(self, mock_run, analyzer, mock_client):
        mock_run.return_value = {
            "SchemaVersion": 2,
            "Results": [
                {
                    "Target": "alpine:latest (alpine 3.19.1)",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2023-1234",
                            "PkgName": "libssl",
                            "InstalledVersion": "1.1.1",
                            "Severity": "CRITICAL",
                        },
                        {
                            "VulnerabilityID": "CVE-2023-5678",
                            "PkgName": "bash",
                            "InstalledVersion": "4.0",
                            "Severity": "HIGH",
                        },
                    ],
                }
            ],
        }

        report = analyzer.analyze(mock_client, "library/alpine", "latest")

        assert report["analyzer"] == "trivy"
        assert report["trivy_version"] == "2"
        assert report["vulnerability_count"] == 2
        assert report["critical_count"] == 1
        assert report["high_count"] == 1
        assert report["medium_count"] == 0

        targets = report["targets"]
        assert len(targets) == 1
        assert targets[0]["Target"] == "alpine:latest (alpine 3.19.1)"
        assert len(targets[0]["Vulnerabilities"]) == 2
        assert targets[0]["Vulnerabilities"][0]["VulnerabilityID"] == "CVE-2023-1234"

    @patch("regis_cli.analyzers.trivy._run_trivy")
    def test_analyze_no_vulns(self, mock_run, analyzer, mock_client):
        mock_run.return_value = {
            "SchemaVersion": 2,
            "Results": [{"Target": "foo", "Vulnerabilities": None}],
        }

        report = analyzer.analyze(mock_client, "library/alpine", "latest")

        assert report["vulnerability_count"] == 0
        assert report["critical_count"] == 0
        assert report["targets"][0]["Vulnerabilities"] is None

    @patch("regis_cli.analyzers.trivy._run_trivy")
    def test_analyze_custom_registry(self, mock_run, analyzer):
        client = MagicMock()
        client.registry = "my.registry.com"

        mock_run.return_value = {"SchemaVersion": 2, "Results": []}

        analyzer.analyze(client, "my-repo", "v1")

        mock_run.assert_called_with(
            "my.registry.com/my-repo:v1",
            username=client.username,
            password=client.password,
            platform=None,
        )
