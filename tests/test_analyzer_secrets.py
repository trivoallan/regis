"""Tests for the secrets analyzer (trufflehog backend)."""

from unittest.mock import MagicMock, patch

import pytest

from regis.analyzers.base import AnalyzerError
from regis.analyzers.secrets import SecretsAnalyzer

_FINDINGS = [
    {
        "DetectorName": "AWS",
        "Verified": True,
        "Redacted": "AKIA...",
        "SourceMetadata": {"Data": {"Docker": {"layer": "sha256:abc"}}},
    },
    {
        "DetectorName": "Generic",
        "Verified": False,
        "Redacted": "xyz...",
        "SourceMetadata": {"Data": {"Docker": {"layer": "sha256:def"}}},
    },
]


@pytest.fixture
def analyzer():
    return SecretsAnalyzer()


class TestSecretsAnalyzer:
    def test_default_rules_slug(self, analyzer):
        slugs = {r["slug"] for r in analyzer.default_rules()}
        assert "secret-scan" in slugs

    @patch("regis.analyzers.secrets._scanner_version", return_value="3.95.3")
    @patch("regis.analyzers.secrets.run_trufflehog")
    def test_analyze_counts(self, mock_run, _mock_ver, analyzer):
        mock_run.return_value = _FINDINGS
        client = MagicMock()
        client.registry = "docker.io"
        client.username = None
        client.password = None

        report = analyzer.analyze(client, "library/alpine", "3.20")

        assert report["analyzer"] == "secrets"
        assert report["scanner_version"] == "3.95.3"
        assert report["secrets_count"] == 2
        assert report["verified_count"] == 1
        assert report["findings"][0]["layer"] == "sha256:abc"
        analyzer.validate(report)

    @patch("regis.analyzers.secrets._scanner_version", return_value="3.95.3")
    @patch("regis.analyzers.secrets.run_trufflehog")
    def test_analyze_no_secrets(self, mock_run, _mock_ver, analyzer):
        mock_run.return_value = []
        client = MagicMock()
        client.registry = "example.com"
        client.username = None
        client.password = None
        report = analyzer.analyze(client, "repo", "tag")
        assert report["secrets_count"] == 0
        assert report["verified_count"] == 0
        assert report["findings"] == []
        analyzer.validate(report)

    @patch("regis.analyzers.secrets._scanner_version", return_value="3.95.3")
    @patch("regis.analyzers.secrets.run_trufflehog")
    def test_analyze_forwards_error(self, mock_run, _mock_ver, analyzer):
        mock_run.side_effect = AnalyzerError("boom")
        client = MagicMock()
        client.registry = "example.com"
        with pytest.raises(AnalyzerError, match="boom"):
            analyzer.analyze(client, "repo", "tag")
