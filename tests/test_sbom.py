"""Tests for the SBOM analyzer."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from regis_cli.analyzers.base import AnalyzerError
from regis_cli.analyzers.sbom import SbomAnalyzer, _run_trivy_sbom

# -- Minimal CycloneDX fixture ------------------------------------------------

CYCLONEDX_SAMPLE = {
    "bomFormat": "CycloneDX",
    "specVersion": "1.5",
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


# -- _run_trivy_sbom tests ----------------------------------------------------


class TestRunTrivySbom:
    @patch("regis_cli.analyzers.sbom.shutil.which")
    def test_trivy_not_found(self, mock_which):
        mock_which.return_value = None
        with pytest.raises(AnalyzerError, match="trivy executable not found"):
            _run_trivy_sbom("alpine:latest")

    @patch("regis_cli.analyzers.sbom.shutil.which")
    @patch("regis_cli.analyzers.sbom.subprocess.run")
    def test_success(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/trivy"
        mock_run.return_value.stdout = json.dumps(CYCLONEDX_SAMPLE)

        result = _run_trivy_sbom("alpine:latest")
        assert result["bomFormat"] == "CycloneDX"

        args = mock_run.call_args[0][0]
        assert "cyclonedx" in args
        assert "alpine:latest" in args

    @patch("regis_cli.analyzers.sbom.shutil.which")
    @patch("regis_cli.analyzers.sbom.subprocess.run")
    def test_failure(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/trivy"
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["trivy"], stderr="scan error"
        )
        with pytest.raises(AnalyzerError, match="trivy sbom failed"):
            _run_trivy_sbom("alpine:latest")


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

    @patch("regis_cli.analyzers.sbom._run_trivy_sbom")
    def test_analyze_success(self, mock_run, analyzer, mock_client):
        mock_run.return_value = CYCLONEDX_SAMPLE

        report = analyzer.analyze(mock_client, "library/alpine", "latest")
        analyzer.validate(report)

        assert report["analyzer"] == "sbom"
        assert report["has_sbom"] is True
        assert report["sbom_format"] == "CycloneDX"
        assert report["sbom_version"] == "1.5"
        assert report["total_components"] == 3
        assert report["component_types"]["library"] == 2
        assert report["component_types"]["application"] == 1
        assert report["total_dependencies"] == 2
        assert "Apache-2.0" in report["licenses"]
        assert "Zlib" in report["licenses"]
        assert len(report["components"]) == 3

    @patch("regis_cli.analyzers.sbom._run_trivy_sbom")
    def test_analyze_empty(self, mock_run, analyzer, mock_client):
        mock_run.return_value = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "components": [],
            "dependencies": [],
        }

        report = analyzer.analyze(mock_client, "library/scratch", "latest")
        analyzer.validate(report)

        assert report["has_sbom"] is False
        assert report["total_components"] == 0
        assert report["licenses"] == []

    @patch("regis_cli.analyzers.sbom._run_trivy_sbom")
    def test_analyze_custom_registry(self, mock_run, analyzer):
        client = MagicMock()
        client.registry = "my.registry.com"
        mock_run.return_value = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "components": [],
            "dependencies": [],
        }

        analyzer.analyze(client, "my-repo", "v1")

        mock_run.assert_called_with(
            "my.registry.com/my-repo:v1",
            username=client.username,
            password=client.password,
            platform=None,
        )

    @patch("regis_cli.analyzers.sbom._run_trivy_sbom")
    def test_docker_hub_image_ref(self, mock_run, analyzer, mock_client):
        mock_run.return_value = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "components": [],
            "dependencies": [],
        }

        analyzer.analyze(mock_client, "library/nginx", "1.25")

        # Docker Hub should NOT include registry prefix.
        mock_run.assert_called_with(
            "library/nginx:1.25",
            username=mock_client.username,
            password=mock_client.password,
            platform=None,
        )
