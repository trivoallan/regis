"""Tests for the CVE analyzer (grype backend)."""

from unittest.mock import MagicMock, patch

import pytest

from regis.analyzers.base import AnalyzerError
from regis.analyzers.cve import CveAnalyzer

# Minimal grype JSON: two matches across two artifact types, mixed severities.
_GRYPE = {
    "descriptor": {"name": "grype", "version": "0.112.0"},
    "matches": [
        {
            "vulnerability": {
                "id": "CVE-2024-0001",
                "severity": "Critical",
                "description": "bad thing",
                "fix": {"versions": ["1.2.3"], "state": "fixed"},
            },
            "artifact": {"name": "libfoo", "version": "1.2.2", "type": "apk"},
        },
        {
            "vulnerability": {
                "id": "CVE-2024-0002",
                "severity": "Negligible",
                "description": "",
                "fix": {"versions": [], "state": "not-fixed"},
            },
            "artifact": {"name": "pybar", "version": "0.9", "type": "python"},
        },
    ],
}


@pytest.fixture
def analyzer():
    return CveAnalyzer()


class TestCveAnalyzer:
    def test_default_criteria_slugs(self, analyzer):
        slugs = {r["slug"] for r in analyzer.default_criteria()}
        assert {"fix-available", "cve-count"} <= slugs

    @patch("regis.analyzers.cve.run_grype")
    def test_analyze_counts_and_targets(self, mock_run, analyzer):
        mock_run.return_value = _GRYPE
        client = MagicMock()
        client.registry = "docker.io"
        client.username = None
        client.password = None

        report = analyzer.analyze(client, "library/alpine", "3.20")

        assert report["analyzer"] == "cve"
        assert report["scanner_version"] == "0.112.0"
        assert report["vulnerability_count"] == 2
        assert report["critical_count"] == 1
        assert report["negligible_count"] == 1
        assert report["fixed_count"] == 1
        # Grouped by artifact.type
        targets = {t["Target"]: t for t in report["targets"]}
        assert set(targets) == {"apk", "python"}
        apk_vuln = targets["apk"]["Vulnerabilities"][0]
        assert apk_vuln["VulnerabilityID"] == "CVE-2024-0001"
        assert apk_vuln["PkgName"] == "libfoo"
        assert apk_vuln["FixedVersion"] == "1.2.3"
        # Per-vuln Severity is emitted upper-case (matches dashboard filter).
        assert apk_vuln["Severity"] == "CRITICAL"
        py_vuln = targets["python"]["Vulnerabilities"][0]
        assert py_vuln["Severity"] == "NEGLIGIBLE"
        # Report must validate against the schema.
        analyzer.validate(report)

    @patch("regis.analyzers.cve.run_grype")
    def test_analyze_forwards_error(self, mock_run, analyzer):
        mock_run.side_effect = AnalyzerError("boom")
        client = MagicMock()
        client.registry = "example.com"
        with pytest.raises(AnalyzerError, match="boom"):
            analyzer.analyze(client, "repo", "tag")
