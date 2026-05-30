"""Tests for the SBOM analyzer."""

from unittest.mock import MagicMock, patch

import pytest

from regis.analyzers.sbom import COPYLEFT_LICENSES, SbomAnalyzer

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


# -- SbomAnalyzer tests --------------------------------------------------------


class TestSbomAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return SbomAnalyzer()

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client.registry = "registry-1.docker.io"
        return client

    @patch("regis.analyzers.sbom.run_syft")
    def test_analyze_success(self, mock_run_syft, analyzer, mock_client):
        mock_run_syft.return_value = CYCLONEDX_SAMPLE

        report = analyzer.analyze(mock_client, "library/alpine", "latest")
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

    @patch("regis.analyzers.sbom.run_syft")
    def test_copyleft_licenses_detected(self, mock_run_syft, analyzer, mock_client):
        mock_run_syft.return_value = CYCLONEDX_COPYLEFT_SAMPLE

        report = analyzer.analyze(mock_client, "library/alpine", "latest")
        analyzer.validate(report)

        assert "GPL-3.0-only" in report["copyleft_licenses"]
        assert "LGPL-2.1-only" in report["copyleft_licenses"]
        assert "Apache-2.0" not in report["copyleft_licenses"]
        assert report["copyleft_licenses"] == sorted(report["copyleft_licenses"])

    @patch("regis.analyzers.sbom.run_syft")
    def test_copyleft_licenses_empty_when_none(
        self, mock_run_syft, analyzer, mock_client
    ):
        mock_run_syft.return_value = CYCLONEDX_SAMPLE

        report = analyzer.analyze(mock_client, "library/alpine", "latest")

        assert report["copyleft_licenses"] == []

    def test_copyleft_licenses_constant_contains_key_identifiers(self):
        strong = {"GPL-2.0", "GPL-3.0", "AGPL-3.0", "SSPL-1.0"}
        weak = {"LGPL-2.1", "MPL-2.0", "EPL-2.0", "CDDL-1.0", "EUPL-1.2"}
        assert strong <= COPYLEFT_LICENSES
        assert weak <= COPYLEFT_LICENSES

    def test_default_rules_include_license_blocklist(self, analyzer):
        slugs = {r["slug"] for r in analyzer.default_rules()}
        assert "license-blocklist" in slugs

    def test_license_blocklist_rule_structure(self, analyzer):
        rule = next(
            r for r in analyzer.default_rules() if r["slug"] == "license-blocklist"
        )
        assert "params" in rule
        assert rule["params"]["blocklist"] == []
        assert "condition" in rule
        assert "messages" in rule

    @patch("regis.analyzers.sbom.run_syft")
    def test_analyze_empty(self, mock_run_syft, analyzer, mock_client):
        mock_run_syft.return_value = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "metadata": {
                "tools": {"components": [{"name": "syft", "version": "1.44.0"}]}
            },
            "components": [],
            "dependencies": [],
        }

        report = analyzer.analyze(mock_client, "library/scratch", "latest")
        analyzer.validate(report)

        assert report["has_sbom"] is False
        assert report["total_components"] == 0
        assert report["licenses"] == []

    @patch("regis.analyzers.sbom.run_syft")
    def test_analyze_custom_registry(self, mock_run_syft, analyzer):
        client = MagicMock()
        client.registry = "my.registry.com"
        mock_run_syft.return_value = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "metadata": {
                "tools": {"components": [{"name": "syft", "version": "1.44.0"}]}
            },
            "components": [],
            "dependencies": [],
        }

        analyzer.analyze(client, "my-repo", "v1")

        mock_run_syft.assert_called_with(
            "my.registry.com/my-repo:v1",
            username=client.username,
            password=client.password,
            platform=None,
        )

    @patch("regis.analyzers.sbom.run_syft")
    def test_docker_hub_image_ref(self, mock_run_syft, analyzer, mock_client):
        mock_run_syft.return_value = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "metadata": {
                "tools": {"components": [{"name": "syft", "version": "1.44.0"}]}
            },
            "components": [],
            "dependencies": [],
        }

        analyzer.analyze(mock_client, "library/nginx", "1.25")

        # Docker Hub should NOT include registry prefix.
        mock_run_syft.assert_called_with(
            "library/nginx:1.25",
            username=mock_client.username,
            password=mock_client.password,
            platform=None,
        )
