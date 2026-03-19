"""Tests for the skopeo analyzer."""

import json
from unittest.mock import patch

import pytest

from regis_cli.analyzers.base import AnalyzerError
from regis_cli.analyzers.skopeo import SkopeoAnalyzer


class MockRegistryClient:
    def __init__(self):
        self.registry = "registry-1.docker.io"
        self.username = None
        self.password = None


class TestSkopeoAnalyzer:
    """Test the skopeo analyzer (successor of image analyzer)."""

    @patch("regis_cli.analyzers.skopeo.subprocess.run")
    def test_single_platform_manifest(self, mock_run):
        def side_effect(cmd, **kwargs):
            class MockResponse:
                def __init__(self, stdout):
                    self.stdout = stdout

            if "--config" in cmd:
                return MockResponse(
                    json.dumps(
                        {
                            "config": {"User": "postgres"},
                        }
                    )
                )
            elif "--raw" in cmd:
                return MockResponse(
                    json.dumps(
                        {
                            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                            "layers": [{}, {}],
                        }
                    )
                )
            else:
                return MockResponse(
                    json.dumps(
                        {
                            "Digest": "sha256:123",
                            "Architecture": "amd64",
                            "Os": "linux",
                            "Created": "2024-01-15T10:00:00Z",
                            "Labels": {"maintainer": "test"},
                            "Layers": [{}, {}],
                        }
                    )
                )

        mock_run.side_effect = side_effect
        client = MockRegistryClient()

        analyzer = SkopeoAnalyzer()
        report = analyzer.analyze(client, "library/nginx", "latest")
        analyzer.validate(report)

        assert report["analyzer"] == "skopeo"
        assert report["repository"] == "library/nginx"
        assert report["tag"] == "latest"
        assert len(report["platforms"]) == 1
        assert "inspect" in report

        plat = report["platforms"][0]
        assert plat["architecture"] == "amd64"
        assert plat["os"] == "linux"
        assert plat["layers_count"] == 2
        assert plat["user"] == "postgres"

    @patch("regis_cli.analyzers.skopeo.subprocess.run")
    def test_multi_arch_manifest(self, mock_run):
        def side_effect(cmd, **kwargs):
            class MockResponse:
                def __init__(self, stdout):
                    self.stdout = stdout

            target = cmd[-1]
            if "--config" in cmd:
                if "sha256:amd64digest" in target:
                    return MockResponse(json.dumps({"config": {"User": "root"}}))
                if "sha256:arm64digest" in target:
                    return MockResponse(json.dumps({"config": {"User": "1001"}}))
                return MockResponse("{}")
            elif "--raw" in cmd:
                return MockResponse(
                    json.dumps(
                        {
                            "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
                            "manifests": [
                                {
                                    "digest": "sha256:amd64digest",
                                    "platform": {
                                        "architecture": "amd64",
                                        "os": "linux",
                                    },
                                },
                                {
                                    "digest": "sha256:arm64digest",
                                    "platform": {
                                        "architecture": "arm64",
                                        "os": "linux",
                                        "variant": "v8",
                                    },
                                },
                            ],
                        }
                    )
                )
            else:
                if "sha256:amd64digest" in target:
                    return MockResponse(
                        json.dumps(
                            {
                                "Architecture": "amd64",
                                "Os": "linux",
                                "Created": "2024-01-15T10:00:00Z",
                                "Layers": [{}],
                            }
                        )
                    )
                if "sha256:arm64digest" in target:
                    return MockResponse(
                        json.dumps(
                            {
                                "Architecture": "arm64",
                                "Os": "linux",
                                "Created": "2024-01-15T11:00:00Z",
                                "Layers": [{}, {}],
                            }
                        )
                    )
                # Primary inspect call
                return MockResponse(json.dumps({"Digest": "sha256:indexdigest"}))

        mock_run.side_effect = side_effect
        client = MockRegistryClient()

        analyzer = SkopeoAnalyzer()
        report = analyzer.analyze(client, "library/nginx", "latest")
        analyzer.validate(report)

        assert len(report["platforms"]) == 2

        # Verify users
        plat_amd64 = next(
            p for p in report["platforms"] if p["architecture"] == "amd64"
        )
        assert plat_amd64["user"] == "root"

        plat_arm64 = next(
            p for p in report["platforms"] if p["architecture"] == "arm64"
        )
        assert plat_arm64["user"] == "1001"

    def test_report_missing_field(self):
        analyzer = SkopeoAnalyzer()
        bad_report = {"analyzer": "skopeo", "repository": "test"}
        with pytest.raises(AnalyzerError):
            analyzer.validate(bad_report)

    def test_report_wrong_analyzer_name(self):
        analyzer = SkopeoAnalyzer()
        bad_report = {
            "analyzer": "wrong",
            "repository": "test",
            "tag": "latest",
            "platforms": [],
            "inspect": {},
        }
        with pytest.raises(AnalyzerError):
            analyzer.validate(bad_report)
