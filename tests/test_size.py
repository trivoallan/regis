"""Tests for the size analyzer."""

import json
from unittest.mock import patch

from regis.analyzers.size import SizeAnalyzer, _human_size


class MockRegistryClient:
    def __init__(self, username=None, password=None):
        self.registry = "registry-1.docker.io"
        self.username = username
        self.password = password


class TestHumanSize:
    def test_bytes(self):
        assert _human_size(500) == "500.0 B"

    def test_kb(self):
        assert _human_size(2048) == "2.0 KB"

    def test_mb(self):
        assert _human_size(5 * 1024 * 1024) == "5.0 MB"


class TestSizeAnalyzer:
    @patch("regis.analyzers.size.run_regctl")
    def test_single_manifest(self, mock_run):
        def side_effect(client, args, *a, **k):
            return json.dumps(
                {
                    "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                    "config": {"digest": "sha256:cfg1", "size": 1500},
                    "layers": [
                        {"size": 10000, "digest": "sha256:l1"},
                        {"size": 20000, "digest": "sha256:l2"},
                    ],
                }
            )

        mock_run.side_effect = side_effect
        client = MockRegistryClient()
        analyzer = SizeAnalyzer()
        report = analyzer.analyze(client, "library/nginx", "latest")
        analyzer.validate(report)

        assert report["multi_arch"] is False
        assert report["total_compressed_bytes"] == 31500
        assert report["layer_count"] == 2
        assert len(report["layers"]) == 2

    @patch("regis.analyzers.size.run_regctl")
    def test_multi_arch_manifest(self, mock_run):
        def side_effect(client, args, *a, **k):
            ref = " ".join(args)
            if "sha256:amd64digest" in ref:
                return json.dumps(
                    {
                        "config": {"size": 500},
                        "layers": [{"size": 1000}],
                    }
                )
            if "sha256:arm64digest" in ref:
                return json.dumps(
                    {
                        "config": {"size": 500},
                        "layers": [{"size": 1000}, {"size": 2000}],
                    }
                )

            # Otherwise return index
            return json.dumps(
                {
                    "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
                    "manifests": [
                        {
                            "digest": "sha256:amd64digest",
                            "size": 1500,  # fallback size if per-platform fetch failed
                            "platform": {"architecture": "amd64", "os": "linux"},
                        },
                        {
                            "digest": "sha256:arm64digest",
                            "platform": {"architecture": "arm64", "os": "linux"},
                        },
                    ],
                }
            )

        mock_run.side_effect = side_effect
        client = MockRegistryClient()
        analyzer = SizeAnalyzer()
        report = analyzer.analyze(client, "library/nginx", "latest")
        analyzer.validate(report)

        assert report["multi_arch"] is True
        assert report["layer_count"] == 1  # From amd64 variant
        assert report["total_compressed_bytes"] == 1500
        assert len(report["platforms"]) == 2

    @patch("regis.analyzers.size.run_regctl")
    def test_multi_arch_filters_attestation_manifests(self, mock_run):
        def side_effect(client, args, *a, **k):
            ref = " ".join(args)
            if "sha256:attestdigest" in ref:
                raise AssertionError(
                    "SizeAnalyzer must not fetch attestation manifest digest"
                )
            if "sha256:amd64digest" in ref:
                return json.dumps({"config": {"size": 500}, "layers": [{"size": 1000}]})
            if "sha256:arm64digest" in ref:
                return json.dumps(
                    {"config": {"size": 500}, "layers": [{"size": 1000}, {"size": 2000}]}
                )
            # Default: return index with two real platforms + one attestation entry
            return json.dumps(
                {
                    "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
                    "manifests": [
                        {
                            "digest": "sha256:amd64digest",
                            "platform": {"architecture": "amd64", "os": "linux"},
                        },
                        {
                            "digest": "sha256:arm64digest",
                            "platform": {"architecture": "arm64", "os": "linux"},
                        },
                        {
                            "digest": "sha256:attestdigest",
                            "platform": {"architecture": "unknown", "os": "unknown"},
                        },
                    ],
                }
            )

        mock_run.side_effect = side_effect
        client = MockRegistryClient()
        analyzer = SizeAnalyzer()
        report = analyzer.analyze(client, "library/nginx", "latest")
        analyzer.validate(report)

        assert report["multi_arch"] is True
        assert len(report["platforms"]) == 2
        for plat in report["platforms"]:
            assert "unknown" not in plat["platform"]

    @patch("regis.analyzers.size.run_regctl")
    def test_empty_manifest(self, mock_run):
        def side_effect(client, args, *a, **k):
            return "{}"

        mock_run.side_effect = side_effect
        client = MockRegistryClient()
        analyzer = SizeAnalyzer()
        report = analyzer.analyze(client, "library/nginx", "latest")
        analyzer.validate(report)

        assert report["layer_count"] == 0
