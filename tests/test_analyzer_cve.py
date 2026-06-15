"""Tests for the CVE analyzer (grype backend)."""

import pytest

from regis.analyzers.cve import CveAnalyzer
from regis.core.domain.context import AnalysisContext
from regis.core.domain.errors import ToolError
from regis.core.model.image_reference import ImageReference
from tests.fakes import FakeImageInspector, FakeToolRunner


def _ctx(tools):
    return AnalysisContext(
        image=ImageReference(
            registry="docker.io", repository="library/alpine", tag="3.20"
        ),
        inspector=FakeImageInspector(),
        tools=tools,
    )


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

    def test_analyze_counts_and_targets(self, analyzer):
        report = analyzer.analyze(_ctx(FakeToolRunner(scan_vulnerabilities=_GRYPE)))

        assert report["analyzer"] == "cve"
        assert report["scanner_version"] == "0.112.0"
        assert report["vulnerability_count"] == 2
        assert report["critical_count"] == 1
        assert report["negligible_count"] == 1
        assert report["fixed_count"] == 1
        assert report["repository"] == "library/alpine"
        assert report["tag"] == "3.20"
        targets = {t["Target"]: t for t in report["targets"]}
        assert set(targets) == {"apk", "python"}
        apk_vuln = targets["apk"]["Vulnerabilities"][0]
        assert apk_vuln["VulnerabilityID"] == "CVE-2024-0001"
        assert apk_vuln["FixedVersion"] == "1.2.3"
        assert apk_vuln["Severity"] == "CRITICAL"
        assert targets["python"]["Vulnerabilities"][0]["Severity"] == "NEGLIGIBLE"
        analyzer.validate(report)

    def test_analyze_propagates_tool_error(self, analyzer):
        class _Boom(FakeToolRunner):
            def scan_vulnerabilities(self, image):
                raise ToolError("boom")

        with pytest.raises(ToolError, match="boom"):
            analyzer.analyze(_ctx(_Boom()))


class TestCveSourceFromDescriptor:
    """Unit tests for CveAnalyzer._source_from_descriptor."""

    def test_source_extracted_from_grype_db_status(self):
        import json
        from pathlib import Path

        raw = json.loads(
            (
                Path(__file__).parent / "fixtures" / "grype" / "debian11_json.json"
            ).read_text(encoding="utf-8")
        )
        source = CveAnalyzer._source_from_descriptor(raw.get("descriptor", {}))

        assert source["built_at"] == "2026-05-30T07:21:01Z"
        assert source["version"] == "v6.1.4"
        assert source["checksum"] == (
            "sha256:88f6f4182111eeb714982e5534be5bd8f1f478aafafe83ad6c6fcccf9d015d06"
        )
        assert isinstance(source["fetched_at"], str) and source["fetched_at"]

    def test_source_tolerates_missing_db_status(self):
        source = CveAnalyzer._source_from_descriptor({})
        assert "built_at" not in source
        assert isinstance(source["fetched_at"], str) and source["fetched_at"]
