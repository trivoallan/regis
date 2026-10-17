from unittest.mock import MagicMock

import pytest

from regis.core.domain.analyzers.provenance import ProvenanceAnalyzer
from regis.core.domain.context import AnalysisContext
from regis.core.domain.errors import RegistryError
from regis.core.model.image_reference import ImageReference
from tests.fakes import FakeToolRunner


def _ctx(inspector, *, repository="my-repo", tag="latest"):
    return AnalysisContext(
        image=ImageReference(registry="docker.io", repository=repository, tag=tag),
        inspector=inspector,
        tools=FakeToolRunner(),
    )


class TestProvenanceAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return ProvenanceAnalyzer()

    def test_analyze_success_with_all_indicators(self, analyzer):
        mock_inspector = MagicMock()
        mock_inspector.get_digest.return_value = "sha256:idx"
        mock_inspector.get_referrers.return_value = []
        mock_inspector.list_tags.return_value = ["sha256-idx.sig"]
        mock_inspector.get_manifest.side_effect = [
            {
                "mediaType": "application/vnd.oci.image.index.v1+json",
                "manifests": [{"digest": "sha256:child"}],
            },
            {
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "config": {"digest": "sha256:cfg"},
            },
            {"layers": [{"digest": "sha256:sig"}]},  # legacy .sig tag manifest
        ]
        mock_inspector.get_blob.return_value = {
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

        res = analyzer.analyze(_ctx(mock_inspector))
        assert res["has_provenance"] is True
        assert res["indicators_count"] == 6
        assert res["source_tracked"] is True
        assert res["has_cosign_signature"] is True

    def test_analyze_empty_manifest_index(self, analyzer):
        mock_inspector = MagicMock()
        mock_inspector.get_manifest.return_value = {
            "mediaType": "application/vnd.oci.image.index.v1+json",
            "manifests": [],
        }
        res = analyzer.analyze(_ctx(mock_inspector))
        assert res["indicators_count"] == 0

    def test_analyze_exception_fetching(self, analyzer):
        mock_inspector = MagicMock()
        mock_inspector.get_manifest.side_effect = Exception("fail")
        res = analyzer.analyze(_ctx(mock_inspector, repository="r", tag="t"))
        assert res["has_provenance"] is False

    def test_cosign_fail_silent(self, analyzer):
        mock_inspector = MagicMock()
        mock_inspector.get_digest.return_value = "sha256:idx"
        mock_inspector.get_referrers.side_effect = RegistryError("referrers boom")
        mock_inspector.list_tags.return_value = []
        mock_inspector.get_manifest.return_value = {
            "mediaType": "manifest",
            "config": {"digest": "s:1"},
        }
        mock_inspector.get_blob.return_value = {"config": {"Labels": {}}}
        res = analyzer.analyze(_ctx(mock_inspector, repository="r", tag="t"))
        assert res["has_cosign_signature"] is False
        assert res["signatures_complete"] is None
        assert "referrers boom" in res["signature_gaps"][0]
