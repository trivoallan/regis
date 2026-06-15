"""Tests for the SBOM analyzer."""

import pytest

from regis.analyzers.sbom import COPYLEFT_LICENSES, SbomAnalyzer
from regis.core.domain.context import AnalysisContext
from regis.core.domain.errors import ToolError
from regis.core.model.image_reference import ImageReference
from tests.fakes import FakeImageInspector, FakeToolRunner

# -- CycloneDX fixtures -------------------------------------------------------

CYCLONEDX_COPYLEFT_SAMPLE = {
    "bomFormat": "CycloneDX",
    "specVersion": "1.5",
    "metadata": {"tools": {"components": [{"name": "syft", "version": "1.44.0"}]}},
    "components": [
        {
            "type": "library",
            "name": "bash",
            "version": "5.2",
            "purl": "pkg:apk/alpine/bash@5.2",
            "licenses": [{"license": {"id": "GPL-3.0-only"}}],
        },
        {
            "type": "library",
            "name": "libssl",
            "version": "3.1.4",
            "purl": "pkg:apk/alpine/libssl@3.1.4",
            "licenses": [{"license": {"id": "LGPL-2.1-only"}}],
        },
        {
            "type": "library",
            "name": "openssl",
            "version": "3.1.4",
            "purl": "pkg:apk/alpine/openssl@3.1.4",
            "licenses": [{"license": {"id": "Apache-2.0"}}],
        },
    ],
    "dependencies": [],
}

CYCLONEDX_SAMPLE = {
    "bomFormat": "CycloneDX",
    "specVersion": "1.5",
    "metadata": {"tools": {"components": [{"name": "syft", "version": "1.44.0"}]}},
    "components": [
        {
            "type": "library",
            "name": "openssl",
            "version": "3.1.4",
            "purl": "pkg:apk/alpine/openssl@3.1.4",
            "licenses": [{"license": {"id": "Apache-2.0"}}],
        },
        {
            "type": "library",
            "name": "zlib",
            "version": "1.3",
            "purl": "pkg:apk/alpine/zlib@1.3",
            "licenses": [{"license": {"name": "Zlib"}}],
        },
        {
            "type": "application",
            "name": "alpine:3.19",
            "purl": None,
        },
    ],
    "dependencies": [
        {"ref": "pkg:apk/alpine/openssl@3.1.4", "dependsOn": []},
        {"ref": "pkg:apk/alpine/zlib@1.3", "dependsOn": []},
    ],
}


# -- Helpers ------------------------------------------------------------------


def _sbom_ctx(tools, *, repository="library/nginx", tag="1.27"):
    return AnalysisContext(
        image=ImageReference(registry="docker.io", repository=repository, tag=tag),
        inspector=FakeImageInspector(),
        tools=tools,
    )


# -- SbomAnalyzer tests --------------------------------------------------------


class TestSbomAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return SbomAnalyzer()

    def test_analyze_success(self, analyzer):
        ctx = _sbom_ctx(FakeToolRunner(generate_sbom=CYCLONEDX_SAMPLE))

        report = analyzer.analyze(ctx)
        analyzer.validate(report)

        assert report["analyzer"] == "sbom"
        assert report["has_sbom"] is True
        assert report["scanner_version"] == "1.44.0"
        assert report["sbom_format"] == "CycloneDX"
        assert report["sbom_version"] == "1.5"
        assert report["total_components"] == 3
        assert report["component_types"]["library"] == 2
        assert report["component_types"]["application"] == 1
        assert report["total_dependencies"] == 2
        assert "Apache-2.0" in report["licenses"]
        assert "Zlib" in report["licenses"]
        assert len(report["components"]) == 3
        assert report["repository"] == "library/nginx"
        assert report["tag"] == "1.27"

    def test_copyleft_licenses_detected(self, analyzer):
        ctx = _sbom_ctx(FakeToolRunner(generate_sbom=CYCLONEDX_COPYLEFT_SAMPLE))

        report = analyzer.analyze(ctx)
        analyzer.validate(report)

        assert "GPL-3.0-only" in report["copyleft_licenses"]
        assert "LGPL-2.1-only" in report["copyleft_licenses"]
        assert "Apache-2.0" not in report["copyleft_licenses"]
        assert report["copyleft_licenses"] == sorted(report["copyleft_licenses"])

    def test_copyleft_licenses_empty_when_none(self, analyzer):
        ctx = _sbom_ctx(FakeToolRunner(generate_sbom=CYCLONEDX_SAMPLE))

        report = analyzer.analyze(ctx)

        assert report["copyleft_licenses"] == []

    def test_copyleft_licenses_constant_contains_key_identifiers(self):
        strong = {"GPL-2.0", "GPL-3.0", "AGPL-3.0", "SSPL-1.0"}
        weak = {"LGPL-2.1", "MPL-2.0", "EPL-2.0", "CDDL-1.0", "EUPL-1.2"}
        assert strong <= COPYLEFT_LICENSES
        assert weak <= COPYLEFT_LICENSES

    def test_default_criteria_include_license_blocklist(self, analyzer):
        slugs = {r["slug"] for r in analyzer.default_criteria()}
        assert "license-blocklist" in slugs

    def test_license_blocklist_rule_structure(self, analyzer):
        rule = next(
            r for r in analyzer.default_criteria() if r["slug"] == "license-blocklist"
        )
        assert "params" in rule
        assert rule["params"]["blocklist"] == []
        assert "condition" in rule
        assert "messages" in rule

    def test_analyze_empty(self, analyzer):
        ctx = _sbom_ctx(
            FakeToolRunner(
                generate_sbom={
                    "bomFormat": "CycloneDX",
                    "specVersion": "1.5",
                    "metadata": {
                        "tools": {"components": [{"name": "syft", "version": "1.44.0"}]}
                    },
                    "components": [],
                    "dependencies": [],
                }
            ),
            repository="library/scratch",
        )

        report = analyzer.analyze(ctx)
        analyzer.validate(report)

        assert report["has_sbom"] is False
        assert report["total_components"] == 0
        assert report["licenses"] == []

    def test_analyze_scanner_version_unknown_when_metadata_absent(self, analyzer):
        ctx = _sbom_ctx(
            FakeToolRunner(
                generate_sbom={
                    "bomFormat": "CycloneDX",
                    "specVersion": "1.6",
                    "components": [],
                }
            ),
            repository="library/alpine",
            tag="3.20",
        )

        report = analyzer.analyze(ctx)
        analyzer.validate(report)

        assert report["scanner_version"] == "unknown"

    def test_analyze_propagates_tool_error(self):
        class _Boom(FakeToolRunner):
            def generate_sbom(self, image):
                raise ToolError("syft down")

        with pytest.raises(ToolError, match="syft down"):
            SbomAnalyzer().analyze(_sbom_ctx(_Boom()))
