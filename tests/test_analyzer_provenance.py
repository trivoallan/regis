from unittest.mock import MagicMock

import pytest

from regis_cli.analyzers.provenance import ProvenanceAnalyzer


class TestProvenanceAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return ProvenanceAnalyzer()

    def test_analyze_success_with_all_indicators(self, analyzer):
        mock_client = MagicMock()
        mock_client.get_manifest.side_effect = [
            {
                "mediaType": "application/vnd.oci.image.index.v1+json",
                "manifests": [{"digest": "sha256:child"}],
            },
            {
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "config": {"digest": "sha256:cfg"},
            },
            {"layers": [{"digest": "sha256:sig"}]},  # cosign signature check
        ]
        mock_client.get_blob.return_value = {
            "config": {
                "Labels": {
                    "org.opencontainers.image.source": "https://github.com/org/repo",
                    "org.opencontainers.image.revision": "abc123",
                    "org.opencontainers.image.created": "2023-01-01T00:00:00Z",
                    "org.opencontainers.image.vendor": "MyVendor",
                    "org.mobyproject.buildkit.source.ref": "my-ref",
                }
            }
        }

        res = analyzer.analyze(mock_client, "my-repo", "latest")
        assert res["has_provenance"] is True
        assert res["indicators_count"] == 6
        assert res["source_tracked"] is True
        assert res["has_cosign_signature"] is True

    def test_analyze_empty_manifest_index(self, analyzer):
        mock_client = MagicMock()
        mock_client.get_manifest.return_value = {
            "mediaType": "application/vnd.oci.image.index.v1+json",
            "manifests": [],
        }
        res = analyzer.analyze(mock_client, "my-repo", "latest")
        assert res["indicators_count"] == 0

    def test_analyze_exception_fetching(self, analyzer):
        mock_client = MagicMock()
        mock_client.get_manifest.side_effect = Exception("fail")
        res = analyzer.analyze(mock_client, "r", "t")
        assert res["has_provenance"] is False

    def test_cosign_fail_silent(self, analyzer):
        mock_client = MagicMock()
        mock_client.get_manifest.side_effect = [
            {"mediaType": "manifest", "config": {"digest": "s:1"}},
            Exception("cosign fail"),
        ]
        mock_client.get_blob.return_value = {"config": {"Labels": {}}}
        res = analyzer.analyze(mock_client, "r", "t")
        assert res["has_cosign_signature"] is False
